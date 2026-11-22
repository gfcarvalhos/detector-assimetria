"""Filtro temporal: suavização (EMA), amplitude de movimento e persistência do alerta."""
from collections import defaultdict, deque

import numpy as np

from src.config.config import LIMITES_BASE, ANGULOS_PARES
from src.geometry.metrics import avaliar


class AnalisadorTempoReal:
    """EMA nas medidas, amplitude de movimento numa janela e persistência do alerta."""

    def __init__(self, alpha=0.35, janela_s=3.0, rom_min=15, n_persist=12, frac=0.6):
        self.alpha, self.janela_s, self.rom_min, self.frac = alpha, janela_s, rom_min, frac
        self.suavizar = True
        self.ema = {}
        self.hist = defaultdict(deque)
        self.flags = defaultdict(lambda: deque(maxlen=n_persist))

    def atualizar(self, m, t, fator=1.0):
        for k, v in m.items():
            if v is None:
                self.ema.pop(k, None)
            else:
                ant = self.ema.get(k)
                self.ema[k] = v if ant is None else self.alpha * v + (1 - self.alpha) * ant
        ema = {k: self.ema.get(k) for k in m}
        usar = ema if self.suavizar else m
        linhas = avaliar(usar, fator)

        for nome in ANGULOS_PARES:
            e, d = usar.get(nome + '_E'), usar.get(nome + '_D')
            hq = self.hist[nome]
            if e is not None and d is not None:
                hq.append((t, e, d))
            while hq and t - hq[0][0] > self.janela_s:
                hq.popleft()
            if len(hq) >= 5:
                arr = np.array(hq)[:, 1:]
                rom_e, rom_d = float(np.ptp(arr[:, 0])), float(np.ptp(arr[:, 1]))
                if max(rom_e, rom_d) >= self.rom_min:
                    diff = abs(rom_e - rom_d)
                    lim = LIMITES_BASE['amplitude'] * fator
                    linhas.append(dict(chave='amp_' + nome, nome='Amplitude ' + nome, e=rom_e, d=rom_d,
                                       diff=diff, limite=lim, assim=diff > lim))

        if self.suavizar:
            for l in linhas:
                hf = self.flags[l['chave']]
                hf.append(l['assim'])
                l['assim'] = len(hf) >= 5 and sum(hf) / len(hf) >= self.frac
        return linhas, ema
