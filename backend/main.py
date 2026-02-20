from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from chat_routes import router as chat_router
from ai_chat_routes import router as ai_chat_router
from guest_chat_routes import router as guest_router
from upload_routes import router as upload_router
from places_routes import router as places_router
from upload_routes import set_models
from guest_chat_routes import set_guest_models
import numpy as np
import tensorflow as tf
from PIL import Image, UnidentifiedImageError
import io

from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as filter_preprocess
from tensorflow.keras.applications.resnet50 import preprocess_input as severity_preprocess

# DB + Auth imports
from database import Base, engine
from auth_routes import router as auth_router

app = FastAPI()

app.include_router(chat_router)
app.include_router(ai_chat_router)
app.include_router(guest_router)
app.include_router(upload_router)
app.include_router(places_router)

# Create DB tables
Base.metadata.create_all(bind=engine)

# -------------------- CORS (React) --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later set to ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth routes
app.include_router(auth_router)

# -------------------- Config --------------------
IMG_SIZE = 224

SEVERITY_CLASSES = ["high", "low", "medium"]
FILTER_CLASSES = ["foot", "random"]

FOOT_ACCEPT_THRESHOLD = 0.95

# -------------------- Load Models --------------------
FILTER_MODEL_PATH = "./models/dfu_filter_mobilenetv2.h5"
SEVERITY_MODEL_PATH = "./models/resnet50_3class_phase2_best.h5"

try:
    foot_random_model = tf.keras.models.load_model(FILTER_MODEL_PATH, compile=False)
    print("Foot/Random filter model loaded!")
except Exception as e:
    print("Failed to load filter model:", e)
    raise e

try:
    severity_model = tf.keras.models.load_model(SEVERITY_MODEL_PATH, compile=False)
    print("ResNet severity model loaded!")
except Exception as e:
    print("Failed to load severity model:", e)
    raise e

# Inject models into both upload_routes and guest_chat_routes
set_models(foot_random_model, severity_model)
set_guest_models(foot_random_model, severity_model)

# -------------------- Helpers --------------------
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


def get_filter_probs(x):
    raw = foot_random_model.predict(x, verbose=0)
    raw = np.array(raw)

    if raw.shape[-1] == 1:
        p_pos = float(raw[0][0])
        p_random = p_pos
        p_foot = 1.0 - p_random
        return p_foot, p_random

    probs = softmax_probs(raw)

    p_foot = float(probs[0])
    p_random = float(probs[1])

    return p_foot, p_random


def get_severity_probs(x):
    raw = severity_model.predict(x, verbose=0)
    probs = softmax_probs(raw)
    return probs


# -------------------- Routes --------------------
@app.get("/")
def home():
    return {"message": "API running. Use POST /predict and /auth/*"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "filter_model_loaded": True,
        "severity_model_loaded": True,
        "foot_accept_threshold": FOOT_ACCEPT_THRESHOLD,
        "severity_classes": SEVERITY_CLASSES,
        "filter_classes": FILTER_CLASSES
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Only JPG/PNG images are allowed.")

    try:
        contents = await file.read()
        pil_img = Image.open(io.BytesIO(contents))
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Invalid image file or corrupted image.")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read image.")

    x = preprocess_image(pil_img)

    x_filter = filter_preprocess(x.copy())
    p_foot, p_random = get_filter_probs(x_filter)

    print(f"[FILTER] p_foot={p_foot:.4f}, p_random={p_random:.4f}")

    if p_foot < FOOT_ACCEPT_THRESHOLD:
        return {
            "status": "REJECTED",
            "message": "Rejected: This image does not look like a foot. Upload a clear foot/DFU image.",
            "dfu_filter": {
                "predicted": "random",
                "p_foot": round(p_foot, 6),
                "p_random": round(p_random, 6),
                "foot_accept_threshold": FOOT_ACCEPT_THRESHOLD
            }
        }

    x_sev = severity_preprocess(x.copy())
    sev_probs = get_severity_probs(x_sev)

    pred_idx = int(np.argmax(sev_probs))
    pred_label = SEVERITY_CLASSES[pred_idx]
    confidence = float(sev_probs[pred_idx])

    probs_dict = {SEVERITY_CLASSES[i]: float(sev_probs[i]) for i in range(len(SEVERITY_CLASSES))}

    return {
        "status": "ACCEPTED",
        "message": "Foot image accepted. Severity predicted successfully.",
        "dfu_filter": {
            "predicted": "foot",
            "p_foot": round(p_foot, 6),
            "p_random": round(p_random, 6),
            "foot_accept_threshold": FOOT_ACCEPT_THRESHOLD
        },
        "predicted_severity": pred_label,
        "confidence": round(confidence, 6),
        "probabilities": probs_dict
    }