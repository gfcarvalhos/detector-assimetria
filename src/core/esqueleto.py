"""Desenho do esqueleto sobre o frame (OpenCV)."""
import cv2

from src.config.config import VIS_MIN, DESTAQUE, CONEXOES
from src.geometry.metrics import pts_px


def desenhar_esqueleto(bgr, lms, linhas):
    out = bgr.copy()
    h, w = out.shape[:2]
    P, V = pts_px(lms, w, h)
    vermelhos = set()
    for l in linhas:
        if l['assim']:
            for a, b in DESTAQUE.get(l['chave'].replace('amp_', ''), []):
                vermelhos.update({(a, b), (b, a)})
    for a, b in CONEXOES:
        if V[a] >= VIS_MIN and V[b] >= VIS_MIN:
            cor = (0, 0, 255) if (a, b) in vermelhos else (0, 220, 0)  # BGR
            cv2.line(out, tuple(P[a].astype(int)), tuple(P[b].astype(int)), cor, 3, cv2.LINE_AA)
    for i in range(11, 33):
        if V[i] >= VIS_MIN:
            cor = (255, 150, 80) if i % 2 == 1 else (45, 150, 255)  # BGR: azul = E, laranja = D
            cv2.circle(out, tuple(P[i].astype(int)), 5, cor, -1, cv2.LINE_AA)
    return out
