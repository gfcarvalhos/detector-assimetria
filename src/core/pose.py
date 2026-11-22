"""MediaPipe Pose: download do modelo e criação do detector (33 landmarks)."""
import urllib.request

from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from src.config.config import MODEL_URL, MODEL_PATH


def baixar_modelo():
    if not MODEL_PATH.exists():
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        print('Baixando modelo de pose...')
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)


def criar_landmarker():
    with open(MODEL_PATH, 'rb') as f:
        modelo = f.read()

    opts = vision.PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_buffer=modelo),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return vision.PoseLandmarker.create_from_options(opts)