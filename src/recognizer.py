
from functools import lru_cache
from pathlib import Path

import numpy as np
import torch
from PIL import Image

try:
    from .train import CRNN
except ImportError:
    from train import CRNN


MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "trained_models"
    / "crnn_final.pt"
)


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Файл модели не найден: {MODEL_PATH}"
        )

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    try:
        checkpoint = torch.load(
            MODEL_PATH,
            map_location=device,
            weights_only=True
        )
    except TypeError:
        checkpoint = torch.load(
            MODEL_PATH,
            map_location=device
        )

    chars = checkpoint["chars"]
    img_h = checkpoint["img_h"]
    max_w = checkpoint["max_w"]

    model = CRNN(len(chars) + 1)
    model.load_state_dict(checkpoint["model"])
    model.to(device)
    model.eval()

    idx2char = {
        i + 1: char for i, char in enumerate(chars)
    }

    print(f"Модель загружена: {MODEL_PATH.name}")
    print(f"Устройство: {device}")

    return model, device, idx2char, img_h, max_w


def recognize(image: Image.Image) -> str:
    model, device, idx2char, img_h, max_w = load_model()

    image = image.convert("L")

    w, h = image.size
    new_w = min(max(round(w * img_h / h), 32), max_w)

    resampling = getattr(Image, "Resampling", Image)
    image = image.resize(
        (new_w, img_h),
        resampling.BILINEAR
    )

    x = np.array(image, dtype=np.float32) / 255.0
    x = (x - 0.5) / 0.5

    x = torch.from_numpy(x).unsqueeze(0).unsqueeze(0)
    x = x.to(device)

    with torch.inference_mode():
        logits = model(x)

    predictions = logits.argmax(2)[:, 0].cpu().tolist()

    result = []
    previous = 0

    for index in predictions:
        if index != 0 and index != previous:
            result.append(idx2char[index])

        previous = index

    return "".join(result)
