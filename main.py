import argparse
import time
from collections import deque

import cv2
import pygame
import mediapipe as mp

from src.config.config import CAM_W, CAM_H, PAINEL_W, RODAPE_H, COR, CHAVES_MED, PASTA_PRINTS
from src.config.setup import inicializar_recursos, inicializar_estado
from src.config.capture import abrir_captura, ler_frame
from src.geometry.metrics import medir, avaliar, nota_simetria


def interative_application(recurso, estado):
  frame = anot = None
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


def main():
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