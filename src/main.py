import argparse
import time
from collections import deque

import cv2
import pygame
import mediapipe as mp

from config.config import CAM_W, CAM_H, PAINEL_W, RODAPE_H, COR, CHAVES_MED, PASTA_PRINTS
from config.capture import abrir_captura, ler_frame
from pose.pose import baixar_modelo, criar_landmarker