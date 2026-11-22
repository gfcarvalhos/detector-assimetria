"""Geometria e métricas: landmarks -> ângulos -> diferenças E x D -> veredito.
Só depende de numpy (testável sem câmera e sem MediaPipe)."""
import math

import numpy as np

from src.config.config import VIS_MIN, LIMITES_BASE, ANGULOS_PARES, INCLINACOES


def pts_px(lms, w, h):
    P = np.array([[l.x * w, l.y * h] for l in lms], dtype=float)
    V = np.array([getattr(l, 'visibility', 1.0) or 0.0 for l in lms], dtype=float)
    return P, V


def ang3(a, b, c):
    ba, bc = a - b, c - b
    cos = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-9)
    return math.degrees(math.acos(np.clip(cos, -1.0, 1.0)))


def inclinacao(pE, pD):
    """> 0 => lado esquerdo mais baixo. |dx| faz funcionar de frente e de costas."""
    dx, dy = pE[0] - pD[0], pE[1] - pD[1]
    return math.degrees(math.atan2(dy, abs(dx) + 1e-9))


def medir(lms, w, h):
    """Medidas brutas a partir dos 33 landmarks (None se pontos pouco visíveis)."""
    P, V = pts_px(lms, w, h)
    ok = lambda *ids: all(V[i] >= VIS_MIN for i in ids)
    m = {'incl_ombros': inclinacao(P[11], P[12]) if ok(11, 12) else None,
         'incl_quadril': inclinacao(P[23], P[24]) if ok(23, 24) else None,
         'incl_tronco': None}
    if ok(11, 12, 23, 24):
        ms, mh = (P[11] + P[12]) / 2, (P[23] + P[24]) / 2
        m['incl_tronco'] = math.degrees(math.atan2(ms[0] - mh[0], mh[1] - ms[1]))
    for nome, (ie, idd) in ANGULOS_PARES.items():
        m[nome + '_E'] = ang3(*P[list(ie)]) if ok(*ie) else None
        m[nome + '_D'] = ang3(*P[list(idd)]) if ok(*idd) else None
    return m


def avaliar(m, fator=1.0):
    """Medidas -> linhas de relatório com diferença, limite e veredito."""
    lim = {k: v * fator for k, v in LIMITES_BASE.items()}
    linhas = []
    for k, nome in INCLINACOES:
        v = m.get(k)
        if v is None:
            continue
        linhas.append(dict(chave=k, nome=nome, valor=v, diff=abs(v), limite=lim[k], assim=abs(v) > lim[k]))
    for nome in ANGULOS_PARES:
        e, d = m.get(nome + '_E'), m.get(nome + '_D')
        if e is None or d is None:
            continue
        diff = abs(e - d)
        si = 100 * diff / ((e + d) / 2 + 1e-9)  # Índice de Simetria (Robinson)
        linhas.append(dict(chave=nome, nome=nome, e=e, d=d, diff=diff, si=si,
                           limite=lim['par'], assim=diff > lim['par']))
    return linhas


def nota_simetria(linhas):
    """0-100%: cada métrica vale 1 com diferença 0 e cai a 0 com o dobro do limite."""
    if not linhas:
        return None
    return 100 * float(np.mean([max(0.0, 1 - l['diff'] / (2 * l['limite'])) for l in linhas]))
