"""Log por frame (CSV) e resumo: FPS, latência, estabilidade e taxa de acerto."""
import csv
import time

import numpy as np

from src.config.config import PASTA_LOGS, CHAVES_MED, CHAVES_FLAG


class Registro:
    def __init__(self, pasta=PASTA_LOGS):
        pasta.mkdir(parents=True, exist_ok=True)
        base = pasta / ('sessao_' + time.strftime('%Y%m%d_%H%M%S'))
        self.csv_path, self.resumo_path = f'{base}.csv', f'{base}_resumo.txt'
        campos = (['t_s', 'fps', 'lat_captura_ms', 'lat_mediapipe_ms', 'lat_proc_ms', 'pessoa', 'suavizacao',
                   'fator_limite', 'rotulo', 'nota', 'assimetria', 'assimetria_bruta']
                  + CHAVES_MED + [k + '_suav' for k in CHAVES_MED] + ['flag_' + k for k in CHAVES_FLAG])
        self.f = open(self.csv_path, 'w', newline='', encoding='utf-8')
        self.w = csv.DictWriter(self.f, fieldnames=campos, restval='')
        self.w.writeheader()
        self.linhas = []

    def add(self, row):
        self.w.writerow({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()})
        self.linhas.append(row)

    def fechar(self):
        self.f.close()
        txt = resumo(self.linhas)
        with open(self.resumo_path, 'w', encoding='utf-8') as f:
            f.write(txt)
        print(txt)
        print(f'Log por frame: {self.csv_path}\nResumo: {self.resumo_path}')


def _jitter(rows, sufixo):
    """Média da variação frame a frame (graus) das medidas — menor = mais estável."""
    vals = []
    for k in CHAVES_MED:
        serie = [r.get(k + sufixo) for r in rows]
        for a, b in zip(serie, serie[1:]):
            if a is not None and b is not None:
                vals.append(abs(b - a))
    return float(np.mean(vals)) if vals else float('nan')


def _trocas_por_min(rows, chave):
    s = [r[chave] for r in rows if r[chave] is not None]
    dur = (rows[-1]['t_s'] - rows[0]['t_s']) / 60 if len(rows) > 1 else 0
    trocas = sum(a != b for a, b in zip(s, s[1:]))
    return trocas / dur if dur > 0 else float('nan')


def resumo(rows):
    if not rows:
        return 'Nenhum frame processado.\n'
    fps = np.array([r['fps'] for r in rows[5:]] or [rows[0]['fps']])
    proc = np.array([r['lat_proc_ms'] for r in rows])
    mpl = np.array([r['lat_mediapipe_ms'] for r in rows])
    com = [r for r in rows if r['pessoa']]
    L = ['=' * 60, 'RESUMO DE DESEMPENHO', '=' * 60,
         f'Frames: {len(rows)}  ·  com pessoa: {len(com)} ({100 * len(com) / len(rows):.0f}%)',
         f'Duração: {rows[-1]["t_s"] - rows[0]["t_s"]:.1f} s', '',
         '[FPS]',
         f'  média {fps.mean():.1f}  ·  mediana {np.median(fps):.1f}  ·  mín {fps.min():.1f}  ·  máx {fps.max():.1f}', '',
         '[Latência]  (frame capturado -> tela atualizada)',
         f'  processamento: média {proc.mean():.1f} ms  ·  p50 {np.percentile(proc, 50):.1f}  ·  '
         f'p95 {np.percentile(proc, 95):.1f}  ·  máx {proc.max():.1f}',
         f'  só MediaPipe:  média {mpl.mean():.1f} ms  ·  p95 {np.percentile(mpl, 95):.1f}', '',
         '[Estabilidade]',
         f'  variação média por frame:  bruto {_jitter(com, ""):.2f}°  ·  suavizado {_jitter(com, "_suav"):.2f}°',
         f'  trocas do alerta por minuto: sem filtro {_trocas_por_min(com, "assimetria_bruta"):.1f}  ·  '
         f'com o que foi exibido {_trocas_por_min(com, "assimetria"):.1f}', '']
    rot = [r for r in com if r['rotulo'] in ('simetrico', 'assimetrico') and r['assimetria'] is not None]
    L.append('[Taxa de acerto]  (frames rotulados com as teclas 1 / 2)')
    if not rot:
        L.append('  Nenhum frame rotulado. Use 1 (simétrica) e 2 (assimétrica) durante a sessão.')
    else:
        vp = sum(r['rotulo'] == 'assimetrico' and r['assimetria'] for r in rot)
        vn = sum(r['rotulo'] == 'simetrico' and not r['assimetria'] for r in rot)
        fp = sum(r['rotulo'] == 'simetrico' and r['assimetria'] for r in rot)
        fn = sum(r['rotulo'] == 'assimetrico' and not r['assimetria'] for r in rot)
        prec = vp / (vp + fp) if vp + fp else float('nan')
        rec = vp / (vp + fn) if vp + fn else float('nan')
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else float('nan')
        L += [f'  frames rotulados: {len(rot)}',
              f'  acurácia {100 * (vp + vn) / len(rot):.1f}%  ·  precisão {100 * prec:.1f}%  ·  '
              f'recall {100 * rec:.1f}%  ·  F1 {100 * f1:.1f}%',
              '  matriz de confusão (linhas = real, colunas = previsto):',
              '                   prev. simétrico   prev. assimétrico',
              f'    real simétrico   {vn:>12}   {fp:>16}',
              f'    real assimétrico {fn:>12}   {vp:>16}']
    L.append('=' * 60)
    return '\n'.join(L) + '\n'
