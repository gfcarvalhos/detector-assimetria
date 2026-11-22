from src.models.classes import Recursos, Estado
import argparse, pygame, time
from collections import deque

from .config import CAM_W, CAM_H, PAINEL_W, RODAPE_H, COR, CHAVES_MED, PASTA_PRINTS
from src.core.pose import baixar_modelo, criar_landmarker
from .capture import abrir_captura
from src.core.realTimeAnalyser import AnalisadorTempoReal
from src.core.register import Registro

def inicializar_recursos():
  ap = argparse.ArgumentParser(description='Detector de Movimentos Assimétricos')
  ap.add_argument('--camera', type=int, default=0)
  ap.add_argument('--video', type=str, default=None, help='usar arquivo de vídeo em vez da webcam')
  args = ap.parse_args()
  
  baixar_modelo()
  cap = abrir_captura(args.camera, args.video)
  
  pygame.init()
  tela = pygame.display.set_mode((CAM_W + PAINEL_W, CAM_H + RODAPE_H))
  pygame.display.set_caption('Detector de Movimentos Assimétricos')
  F = {'p': pygame.font.SysFont('arial', 15), 'b': pygame.font.SysFont('arial', 16, bold=True),
  'h2': pygame.font.SysFont('arial', 22, bold=True), 'grande': pygame.font.SysFont('arial', 54, bold=True)}
     
  lm = criar_landmarker()
  rt = AnalisadorTempoReal()
  reg = Registro()
  PASTA_PRINTS.mkdir(exist_ok=True)

  return Recursos(args, cap, lm, rt, tela, reg);


def inicializar_estado(recursos):
  controles = dict(suavizar=True, espelhar=not recursos.args.video, fator=1.0, rotulo=None, pausado=False,
                  gravando=recursos.reg.csv_path)
  perf = dict(fps=0.0, proc=0.0, mp=0.0, leit=0.0)
  hist_fps = deque(maxlen=150)
  msg = None
  t_inicio = time.perf_counter()
  t_ant = None
  ts_ant = -1
  frame = anot = None

  return Estado(controles, perf, hist_fps, msg, t_inicio, t_ant, ts_ant, frame, anot)