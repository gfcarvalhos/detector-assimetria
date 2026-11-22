from dataclasses import dataclass
import argparse

@dataclass
class Recursos:
    args: argparse.Namespace
    cap: object
    lm: object
    rt: object
    tela: object
    fontes: dict
    reg: object


@dataclass
class Estado:
    controles: dict
    perf: dict
    hist_fps: object
    msg: object
    t_inicio: float
    t_ant: object
    ts_ant: int
    frame: object
    anot: object