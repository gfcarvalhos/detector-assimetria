"""Captura de vídeo com OpenCV (webcam ou arquivo)."""
import cv2

from . import CAM_W, CAM_H


def abrir_captura(camera=0, video=None):
    cap = cv2.VideoCapture(video if video else camera)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # reduz latência em câmeras que respeitam o ajuste
    if not cap.isOpened():
        raise SystemExit('Não consegui abrir a câmera/vídeo.')
    return cap


def ler_frame(cap):
    """Retorna (ok, frame) já no tamanho CAM_W x CAM_H."""
    ok, frame = cap.read()
    if ok and frame.shape[:2] != (CAM_H, CAM_W):
        frame = cv2.resize(frame, (CAM_W, CAM_H))
    return ok, frame
