import numpy as np
from PIL import Image
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as filter_preprocess
from tensorflow.keras.applications.resnet50 import preprocess_input as severity_preprocess

IMG_SIZE = 224
SEVERITY_CLASSES = ["high", "low", "medium"]
FOOT_ACCEPT_THRESHOLD = 0.95


def preprocess_image(pil_img):
    pil_img = pil_img.convert("RGB").resize((IMG_SIZE, IMG_SIZE))
    x = np.array(pil_img).astype(np.float32)
    x = np.expand_dims(x, axis=0)
    return x


def softmax_probs(logits_or_probs):
    arr = np.array(logits_or_probs)

    if arr.ndim == 2:
        arr = arr[0]

    s = float(np.sum(arr))
    if 0.95 <= s <= 1.05:
        return arr

    exp = np.exp(arr - np.max(arr))
    return exp / np.sum(exp)


def get_filter_probs(foot_random_model, x):
    raw = foot_random_model.predict(x, verbose=0)
    raw = np.array(raw)

    # sigmoid (1,1)
    if raw.shape[-1] == 1:
        p_pos = float(raw[0][0])
        p_random = p_pos
        p_foot = 1.0 - p_random
        return p_foot, p_random

    # softmax (1,2)
    probs = softmax_probs(raw)
    p_foot = float(probs[0])
    p_random = float(probs[1])
    return p_foot, p_random


def get_severity_probs(severity_model, x):
    raw = severity_model.predict(x, verbose=0)
    probs = softmax_probs(raw)
    return probs


def predict_ulcer(pil_img, foot_random_model, severity_model):
    x = preprocess_image(pil_img)

    # FILTER
    x_filter = filter_preprocess(x.copy())
    p_foot, p_random = get_filter_probs(foot_random_model, x_filter)

    if p_foot < FOOT_ACCEPT_THRESHOLD:
        return {
            "status": "REJECTED",
            "is_foot": False,
            "p_foot": float(p_foot),
            "p_random": float(p_random),
            "severity": None,
            "confidence": None,
            "probabilities": None
        }

    # SEVERITY
    x_sev = severity_preprocess(x.copy())
    sev_probs = get_severity_probs(severity_model, x_sev)

    pred_idx = int(np.argmax(sev_probs))
    pred_label = SEVERITY_CLASSES[pred_idx]
    confidence = float(sev_probs[pred_idx])

    probs_dict = {SEVERITY_CLASSES[i]: float(sev_probs[i]) for i in range(len(SEVERITY_CLASSES))}

    return {
        "status": "ACCEPTED",
        "is_foot": True,
        "p_foot": float(p_foot),
        "p_random": float(p_random),
        "severity": pred_label,
        "confidence": confidence,
        "probabilities": probs_dict
    }