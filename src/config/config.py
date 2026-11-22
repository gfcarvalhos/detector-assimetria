"""Constantes do projeto: caminhos, limiares, landmarks, cores e layout."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_MODELOS = RAIZ / 'models'
PASTA_LOGS = RAIZ / 'logs'
PASTA_PRINTS = RAIZ / 'prints'

MODEL_URL = ('https://storage.googleapis.com/mediapipe-models/pose_landmarker/'
             'pose_landmarker_full/float16/latest/pose_landmarker_full.task')
MODEL_PATH = PASTA_MODELOS / 'pose_landmarker_full.task'

VIS_MIN = 0.5            # visibilidade mínima de um landmark
CAM_W, CAM_H = 640, 480  # resolução de captura
PAINEL_W = 430           # largura do painel lateral
RODAPE_H = 250           # altura da área abaixo da câmera

# Limiares heurísticos (multiplicados pelo fator de sensibilidade)
LIMITES_BASE = {
    'incl_ombros': 5,    # graus de inclinação da linha dos ombros
    'incl_quadril': 5,   # graus de inclinação da linha do quadril
    'incl_tronco': 7,    # graus de inclinação lateral do tronco
    'par': 15,           # diferença E x D de um ângulo articular
    'amplitude': 20,     # diferença E x D da amplitude de movimento (janela de 3 s)
}

# Ângulo no vértice b de (a, b, c). E = esquerdo DA PESSOA, D = direito
ANGULOS_PARES = {
    'Ombro':    ((23, 11, 13), (24, 12, 14)),   # abdução: quadril-ombro-cotovelo
    'Cotovelo': ((11, 13, 15), (12, 14, 16)),
    'Quadril':  ((11, 23, 25), (12, 24, 26)),
    'Joelho':   ((23, 25, 27), (24, 26, 28)),
}
INCLINACOES = [('incl_ombros', 'Linha dos ombros'),
               ('incl_quadril', 'Linha do quadril'),
               ('incl_tronco', 'Tronco (lateral)')]

DESTAQUE = {
    'incl_ombros': [(11, 12)],
    'incl_quadril': [(23, 24)],
    'incl_tronco': [(11, 23), (12, 24)],
    'Ombro': [(11, 13), (12, 14), (11, 23), (12, 24)],
    'Cotovelo': [(11, 13), (13, 15), (12, 14), (14, 16)],
    'Quadril': [(11, 23), (12, 24), (23, 25), (24, 26)],
    'Joelho': [(23, 25), (25, 27), (24, 26), (26, 28)],
}

CONEXOES = [(0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8), (9, 10),
            (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
            (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
            (11, 23), (12, 24), (23, 24), (23, 25), (25, 27), (27, 29), (29, 31), (27, 31),
            (24, 26), (26, 28), (28, 30), (30, 32), (28, 32)]

CHAVES_MED = [k for k, _ in INCLINACOES] + [f'{n}_{s}' for n in ANGULOS_PARES for s in 'ED']
CHAVES_FLAG = [k for k, _ in INCLINACOES] + list(ANGULOS_PARES) + [f'amp_{n}' for n in ANGULOS_PARES]

# Cores (RGB, pygame)
COR = dict(fundo=(22, 24, 30), card=(34, 37, 46), texto=(232, 234, 238), sub=(150, 156, 168),
           ok=(72, 200, 120), aviso=(240, 190, 60), alerta=(235, 82, 82), trilho=(56, 60, 72),
           esq=(80, 150, 255), dir=(255, 150, 45))
