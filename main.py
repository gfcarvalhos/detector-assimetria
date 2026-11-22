import time, cv2, pygame, sys
import mediapipe as mp

from src.config.config import CAM_W, CAM_H, PAINEL_W, RODAPE_H, COR, CHAVES_MED, PASTA_PRINTS
from src.config.setup import inicializar_recursos, inicializar_estado
from src.config.capture import abrir_captura, ler_frame
from src.geometry.metrics import medir, avaliar, nota_simetria
from src.core.esqueleto import desenhar_esqueleto
from src.core.interface import bgr_para_surface, desenhar_painel, desenhar_rodape
from src.core.image import analisar_imagens


def captura(recurso):
    t0 = time.perf_counter()
    ok, frame = ler_frame(recurso.cap)
    t_cap = time.perf_counter()
    continuar = ok or not recurso.args.video

    return continuar, t0, frame, t_cap

def mediapipe_pose(estado, recurso, t_cap, frame):
    ts = max(int((t_cap - estado.t_inicio) * 1000), estado.ts_ant + 1)  # precisa ser crescente
    estado.ts_ant = ts
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = recurso.lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ts)
    t_mp = time.perf_counter()

    return ts, rgb, res, t_mp

def assimetria(recurso, estado, res, t_cap, frame):
    pessoa = bool(res.pose_landmarks)
    m, ema, linhas = {k: None for k in CHAVES_MED}, {}, []
    if pessoa:
        lms = res.pose_landmarks[0]  # 33 landmarks
        m = medir(lms, CAM_W, CAM_H)
        linhas, ema = recurso.rt.atualizar(m, t_cap, estado.controles['fator'])
        anot = desenhar_esqueleto(frame, lms, linhas)
    else:
        anot = frame.copy()
    assim = any(l['assim'] for l in linhas) if pessoa else None
    assim_bruta = any(l['assim'] for l in avaliar(m, estado.controles['fator'])) if pessoa else None
    nota = nota_simetria(linhas) if pessoa else None
    return anot, linhas, nota, assim, pessoa, assim_bruta, ema, m

def resultado_visual(recurso, estado, anot, linhas, nota, assim, pessoa, msg):
    F = recurso.fontes
    recurso.tela.fill(COR['fundo'])
    recurso.tela.blit(bgr_para_surface(cv2.flip(anot, 1) if estado.controles['espelhar'] else anot), (0, 0))
    desenhar_painel(recurso.tela, F, CAM_W, linhas, nota, assim, pessoa)
    desenhar_rodape(recurso.tela, F, CAM_H, estado.perf, estado.controles, estado.hist_fps, msg)
    pygame.display.flip()
    t_fim = time.perf_counter()

    return t_fim

def metricas_desempenho(recurso, estado, t_fim, t_cap, t0, t_mp, pessoa, nota, assim, assim_bruta, ema, m, linhas):
    if estado.t_ant is not None and t0 > estado.t_ant:
        fps_inst = 1 / (t0 - estado.t_ant)
        estado.perf['fps'] = fps_inst if estado.perf['fps'] == 0 else 0.9 * estado.perf['fps'] + 0.1 * fps_inst
    estado.t_ant = t0
    estado.perf['proc'] = (t_fim - t_cap) * 1000
    estado.perf['mp'] = (t_mp - t_cap) * 1000
    estado.perf['leit'] = (t_cap - t0) * 1000
    estado.hist_fps.append(estado.perf['fps'])
    
    row = dict(t_s=t_cap - estado.t_inicio, fps=estado.perf['fps'], lat_captura_ms=estado.perf['leit'],
                lat_mediapipe_ms=estado.perf['mp'], lat_proc_ms=estado.perf['proc'], pessoa=int(pessoa),
                suavizacao=int(estado.controles['suavizar']), fator_limite=estado.controles['fator'],
                rotulo=estado.controles['rotulo'], nota=nota, assimetria=assim, assimetria_bruta=assim_bruta)
    row.update({k: m.get(k) for k in CHAVES_MED})
    row.update({k + '_suav': ema.get(k) for k in CHAVES_MED})
    row.update({'flag_' + l['chave']: int(l['assim']) for l in linhas})
    recurso.reg.add(row)

def interative_application(recurso, estado):
  frame = anot = None
  msg = None
  rodando = True
  while rodando:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            rodando = False
        elif ev.type == pygame.KEYDOWN:
            k = ev.key
            if k in (pygame.K_q, pygame.K_ESCAPE):
                rodando = False
            elif k == pygame.K_SPACE:
                estado.controles['pausado'] = not estado.controles['pausado']
            elif k == pygame.K_f:
                estado.controles['suavizar'] = recurso.rt.suavizar = not recurso.rt.suavizar
            elif k == pygame.K_m:
                estado.controles['espelhar'] = not estado.controles['espelhar']
            elif k in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                estado.controles['fator'] = min(3.0, estado.controles['fator'] + 0.1)
            elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
                estado.controles['fator'] = max(0.3, estado.controles['fator'] - 0.1)
            elif k in (pygame.K_1, pygame.K_KP1):
                estado.controles['rotulo'] = 'simetrico'
            elif k in (pygame.K_2, pygame.K_KP2):
                estado.controles['rotulo'] = 'assimetrico'
            elif k in (pygame.K_0, pygame.K_KP0):
                estado.controles['rotulo'] = None
            elif k == pygame.K_s and frame is not None:
                nome = str(PASTA_PRINTS / f'print_{time.strftime("%Y%m%d_%H%M%S")}.jpg')
                cv2.imwrite(nome, frame)
                cv2.imwrite(nome.replace('.jpg', '_anotado.jpg'), anot)
                msg = (f'Print salvo: {nome}', time.time())
    if not rodando:
        break
    if estado.controles['pausado']:
        pygame.time.wait(30)
        continue

    # ---------- Captura (OpenCV) ----------
    continuar, t0, frame, t_cap = captura(recurso)
    if not continuar:
        break
    if frame is None:
        continue

    # ---------- MediaPipe Pose ----------
    ts, rgb, res, t_mp = mediapipe_pose(estado, recurso, t_cap, frame)

    # ---------- Coordenadas -> ângulos -> assimetria ----------
    anot, linhas, nota, assim, pessoa, assim_bruta, ema, m = assimetria(recurso, estado, res, t_cap, frame)

    # ---------- Resultado visual (pygame) ----------
    t_fim = resultado_visual(recurso, estado, anot, linhas, nota, assim, pessoa, msg)

    # ---------- Métricas de desempenho ----------
    metricas_desempenho(recurso, estado, t_fim, t_cap, t0, t_mp, pessoa, nota, assim, assim_bruta, ema, m, linhas)


def main():
  if '--imagem' in sys.argv:
    analisar_imagens(sys.argv[sys.argv.index('--imagem') + 1:])
    return
  recurso = inicializar_recursos();
  estado = inicializar_estado(recurso);
  try:
    interative_application(recurso, estado);
  finally:
        recurso.cap.release()
        recurso.lm.close()
        pygame.quit()
        recurso.reg.fechar()

if __name__ == '__main__':
    main()