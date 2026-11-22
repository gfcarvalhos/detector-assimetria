"""Interface pygame: painel de indicadores de simetria e rodapé de desempenho."""
import time

import cv2
import pygame

from src.config.config import COR, PAINEL_W, CAM_W, RODAPE_H, ANGULOS_PARES, INCLINACOES


def bgr_para_surface(bgr):
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return pygame.image.frombuffer(rgb.tobytes(), (rgb.shape[1], rgb.shape[0]), 'RGB')


def cor_nivel(frac):
    """frac = diff / limite."""
    return COR['ok'] if frac <= 0.7 else COR['aviso'] if frac <= 1.0 else COR['alerta']


def barra(tela, x, y, w, h, frac, cor):
    pygame.draw.rect(tela, COR['trilho'], (x, y, w, h), border_radius=h // 2)
    fw = int(w * max(0.0, min(1.0, frac)))
    if fw > 0:
        pygame.draw.rect(tela, cor, (x, y, fw, h), border_radius=h // 2)


def texto(tela, fonte, s, x, y, cor=None, direita=False):
    surf = fonte.render(s, True, cor or COR['texto'])
    tela.blit(surf, (x - surf.get_width(), y) if direita else (x, y))
    return surf.get_height()


def desenhar_painel(tela, F, x0, linhas, nota, assim, pessoa):
    W = PAINEL_W - 32
    x, y = x0 + 16, 14
    pygame.draw.rect(tela, COR['fundo'], (x0, 0, PAINEL_W, tela.get_height()))
    texto(tela, F['h2'], 'Indicadores de simetria', x, y)
    y += 36

    # Nota geral
    pygame.draw.rect(tela, COR['card'], (x - 8, y - 6, W + 16, 92), border_radius=10)
    if not pessoa or nota is None:
        texto(tela, F['h2'], 'Aguardando pessoa...', x, y + 26, COR['sub'])
    else:
        cor = COR['ok'] if nota >= 80 else COR['aviso'] if nota >= 60 else COR['alerta']
        texto(tela, F['grande'], f'{nota:.0f}%', x, y - 2, cor)
        texto(tela, F['p'], 'nota de simetria', x + 130, y + 8, COR['sub'])
        st = 'ASSIMETRIA DETECTADA' if assim else 'Postura simétrica'
        texto(tela, F['b'], st, x + 130, y + 28, COR['alerta'] if assim else COR['ok'])
        barra(tela, x, y + 64, W, 10, nota / 100, cor)
    y += 100

    idx = {l['chave']: l for l in linhas}

    # Pares articulares: barras E x D
    for nome in ANGULOS_PARES:
        l = idx.get(nome)
        texto(tela, F['b'], nome, x, y)
        if l is None:
            texto(tela, F['p'], 'fora de vista', x + W, y + 2, COR['sub'], direita=True)
            y += 56
            continue
        frac = l['diff'] / l['limite']
        texto(tela, F['b'], f"dif {l['diff']:.0f}°  ·  IS {l['si']:.0f}%", x + W, y, cor_nivel(frac), direita=True)
        y += 22
        for lado, val, cor in (('E', l['e'], COR['esq']), ('D', l['d'], COR['dir'])):
            texto(tela, F['p'], lado, x, y - 3, cor)
            barra(tela, x + 18, y, W - 78, 9, val / 180, cor)
            texto(tela, F['p'], f'{val:.0f}°', x + W, y - 3, direita=True)
            y += 15
        y += 6

    # Inclinações
    y += 4
    texto(tela, F['b'], 'Alinhamento', x, y)
    y += 24
    for k, nome in INCLINACOES:
        l = idx.get(k)
        if l is None:
            texto(tela, F['p'], f'{nome}: fora de vista', x, y, COR['sub'])
        else:
            frac = l['diff'] / l['limite']
            if k == 'incl_tronco':
                lado = '→' if l['valor'] > 0 else '←'
            else:
                lado = 'E mais baixo' if l['valor'] > 0 else 'D mais baixo'
            texto(tela, F['p'], f"{nome}: {l['diff']:.1f}° ({lado})", x, y, cor_nivel(frac))
            barra(tela, x + W - 90, y + 4, 90, 8, frac / 2, cor_nivel(frac))
        y += 20

    # Amplitude de movimento
    amps = [l for l in linhas if l['chave'].startswith('amp_')]
    if amps:
        y += 8
        texto(tela, F['b'], 'Amplitude de movimento (3 s)', x, y)
        y += 24
        for l in amps:
            frac = l['diff'] / l['limite']
            texto(tela, F['p'], f"{l['nome'][10:]}: E {l['e']:.0f}° | D {l['d']:.0f}°  (dif {l['diff']:.0f}°)",
                  x, y, cor_nivel(frac))
            y += 19


def desenhar_rodape(tela, F, y0, perf, estado, hist_fps, msg):
    w = CAM_W
    pygame.draw.rect(tela, COR['card'], (0, y0, w, RODAPE_H))
    x, y = 14, y0 + 10
    texto(tela, F['b'], f"FPS {perf['fps']:.1f}", x, y, COR['ok'] if perf['fps'] >= 20 else COR['aviso'])
    texto(tela, F['p'], f"Latência: proc. {perf['proc']:.0f} ms · MediaPipe {perf['mp']:.0f} ms"
                        f" · captura {perf['leit']:.0f} ms", x + 90, y + 2, COR['sub'])
    y += 26

    # Gráfico do FPS (últimos frames)
    gx, gy, gw, gh = x, y, w - 28, 60
    pygame.draw.rect(tela, COR['fundo'], (gx, gy, gw, gh), border_radius=6)
    if len(hist_fps) > 1:
        top = max(35.0, max(hist_fps))
        pts = [(gx + i * gw / (hist_fps.maxlen - 1), gy + gh - 4 - v / top * (gh - 8)) for i, v in enumerate(hist_fps)]
        pygame.draw.lines(tela, COR['ok'], False, pts, 2)
        texto(tela, F['p'], f'{top:.0f}', gx + gw - 6, gy + 2, COR['sub'], direita=True)
    y += gh + 10

    rot = {None: 'nenhum', 'simetrico': 'SIMÉTRICA', 'assimetrico': 'ASSIMÉTRICA'}[estado['rotulo']]
    texto(tela, F['p'], f"Suavização {'ON' if estado['suavizar'] else 'OFF'} · Limites x{estado['fator']:.1f}"
                        f" · Espelho {'ON' if estado['espelhar'] else 'OFF'} · Rótulo: {rot}", x, y)
    y += 22
    texto(tela, F['p'], 'Q sair · S print · F suavização · M espelho · +/- limites · ESPAÇO pausa', x, y, COR['sub'])
    y += 18
    texto(tela, F['p'], 'Rótulo: 1 simétrica · 2 assimétrica · 0 sem rótulo', x, y, COR['sub'])
    y += 22
    if estado['gravando']:
        texto(tela, F['p'], f"Log: {estado['gravando']}", x, y, COR['sub'])
        y += 20
    if msg and time.time() - msg[1] < 3:
        texto(tela, F['b'], msg[0], x, y, COR['aviso'])
