"""Análise estática: uma ou mais imagens (prints, fotos)."""
import cv2, pygame
import mediapipe as mp
from mediapipe.tasks.python import vision

from src.config.config import CAM_W, CAM_H, PAINEL_W, RODAPE_H, COR, PASTA_PRINTS
from src.core.pose import baixar_modelo, criar_landmarker
from src.geometry.metrics import medir, avaliar, nota_simetria
from src.core.esqueleto import desenhar_esqueleto
from src.core.interface import bgr_para_surface, desenhar_painel


def analisar_imagens(caminhos):
    baixar_modelo()
    lm = criar_landmarker(vision.RunningMode.IMAGE)
    pygame.init()
    tela = pygame.display.set_mode((CAM_W + PAINEL_W, CAM_H))
    F = {'p': pygame.font.SysFont('arial', 15), 'b': pygame.font.SysFont('arial', 16, bold=True),
         'h2': pygame.font.SysFont('arial', 22, bold=True), 'grande': pygame.font.SysFont('arial', 54, bold=True)}
    PASTA_PRINTS.mkdir(exist_ok=True)
    try:
        for caminho in caminhos:
            img = cv2.imread(caminho)
            if img is None:
                print(f'Não consegui abrir {caminho}')
                continue
            img = cv2.resize(img, (CAM_W, CAM_H))
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            res = lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))

            pessoa = bool(res.pose_landmarks)
            linhas, nota, assim, anot = [], None, None, img
            if pessoa:
                lms = res.pose_landmarks[0]
                linhas = avaliar(medir(lms, CAM_W, CAM_H))   # sem filtro temporal
                nota = nota_simetria(linhas)
                assim = any(l['assim'] for l in linhas)
                anot = desenhar_esqueleto(img, lms, linhas)

            print(f'\n{caminho}: nota {nota:.0f}%' if pessoa else f'\n{caminho}: nenhuma pessoa detectada')
            for l in linhas:
                print(f"  {l['nome']:<18} dif {l['diff']:5.1f}°  limite {l['limite']:.0f}°  "
                      f"{'ASSIMÉTRICO' if l['assim'] else 'ok'}")
            cv2.imwrite(str(PASTA_PRINTS / ('anotado_' + caminho.replace('\\', '/').split('/')[-1])), anot)

            tela.fill(COR['fundo'])
            tela.blit(bgr_para_surface(anot), (0, 0))
            desenhar_painel(tela, F, CAM_W, linhas, nota, assim, pessoa)
            pygame.display.flip()

            esperando = True                 # qualquer tecla = próxima imagem; Q = sair
            while esperando:
                ev = pygame.event.wait()
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key in (pygame.K_q, pygame.K_ESCAPE)):
                    return
                if ev.type == pygame.KEYDOWN:
                    esperando = False
    finally:
        lm.close()
        pygame.quit()