# SentinelAI — ML Anomaly Detection Model
# Owner: Akash
# Uses Isolation Forest (unsupervised) to detect anomalous behavioral patterns.
# Train with: python ml_model.py --train
# Predict with: load the saved model and call predict()

from __future__ import annotations

try:
    import numpy as np
    import joblib
    from sklearn.ensemble import IsolationForest
    _ML_AVAILABLE = True
except ImportError:
    # ML dependencies not available - using stub functions
    _ML_AVAILABLE = False
    np = None
    joblib = None
    IsolationForest = None

import os
import argparse
from pathlib import Path

MODEL_PATH = os.getenv("ML_MODEL_PATH", "./ml_model.pkl")

# Feature order — MUST match generate_training_data.py
FEATURE_NAMES = [
    "typing_variance_ms",
    "time_to_complete_sec",
    "mouse_move_count",
    "registrations_from_ip_1h",
    "email_pattern_score",       # 1.0 = clean, 0.0 = disposable/sequential
    "keypress_count",
    "session_actions_per_min",
]

# Stub implementations for when ML is unavailable
def _stub_build_feature_vector(
    typing_variance_ms: float,
    time_to_complete_sec: float,
    mouse_move_count: int,
    registrations_from_ip_1h: int,
    email_pattern_score: float,
    keypress_count: int,
    session_actions_per_min: float,
):
    """Stub that returns a placeholder when numpy is not available."""
    return None


def _stub_predict(feature_vector, model=None) -> float:
    """Stub that returns neutral score when sklearn is not available."""
    return 0.5


def _stub_get_model():
    """Stub that returns None when model cannot be loaded."""
    return None


def build_feature_vector(
    typing_variance_ms: float,
    time_to_complete_sec: float,
    mouse_move_count: int,
    registrations_from_ip_1h: int,
    email_pattern_score: float,
    keypress_count: int,
    session_actions_per_min: float,
) -> any:
    """
    Build a numpy feature vector in the correct order for the model.
    Call this before calling predict().
    """
    if not _ML_AVAILABLE:
        return _stub_build_feature_vector(
            typing_variance_ms, time_to_complete_sec, mouse_move_count,
            registrations_from_ip_1h, email_pattern_score, keypress_count,
            session_actions_per_min
        )
    
    return np.array([[
        typing_variance_ms,
        time_to_complete_sec,
        mouse_move_count,
        registrations_from_ip_1h,
        email_pattern_score,
        keypress_count,
        session_actions_per_min,
    ]])


def train(training_data_path: str = "../scripts/training_data.csv"):
    """
    Train the Isolation Forest on normal user data and save the model.
    Run this once before starting the server.
    """
    import pandas as pd
    from sklearn.ensemble import IsolationForest

    print(f"Loading training data from {training_data_path}...")
    df = pd.read_csv(training_data_path)

    # Train only on benign users (label == 0) — unsupervised approach
    benign_df = df[df["label"] == 0][FEATURE_NAMES]
    print(f"Training on {len(benign_df)} benign samples...")

    model = IsolationForest(
        n_estimators=200,
        contamination=float(os.getenv("ML_CONTAMINATION", "0.1")),
        random_state=42,
        n_jobs=-1,
    )
    model.fit(benign_df.values)

    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

    # Quick sanity check on malicious samples
    malicious_df = df[df["label"] == 1][FEATURE_NAMES]
    preds = model.predict(malicious_df.values)
    flagged = (preds == -1).sum()
    print(f"Sanity check: {flagged}/{len(malicious_df)} malicious samples correctly flagged")


def load_model():
    """Load the saved model. Returns None if model file doesn't exist yet."""
    if not _ML_AVAILABLE:
        return None

    if not Path(MODEL_PATH).exists():
        print(f"Warning: model file not found at {MODEL_PATH}. Run --train first.")
        return None
    return joblib.load(MODEL_PATH)


def predict(feature_vector: np.ndarray, model=None) -> float:
    """
    Predict anomaly score for a single feature vector.
    Returns a score in [-1, 0]:
      - Close to 0   → normal behavior
      - Close to -1  → strong anomaly

    Returns 0.0 (neutral) if model is not loaded.
    """
    if not _ML_AVAILABLE:
        return _stub_predict(feature_vector, model)
    
    if model is None:
        model = load_model()
    if model is None:
        return 0.0

    # score_samples returns negative values; more negative = more anomalous
    raw_score = model.score_samples(feature_vector)[0]

    # Normalize to [-1, 0] range (raw scores are roughly in [-0.5, 0.5])
    normalized = max(-1.0, min(0.0, raw_score))
    return normalized


# Singleton model instance — loaded once on server startup
_model = None

def get_model():
    global _model
    if not _ML_AVAILABLE:
        return _stub_get_model()

    if _model is None:
        _model = load_model()
    return _model


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", action="store_true", help="Train and save the model")
    parser.add_argument("--test", action="store_true", help="Run a quick prediction test")
    args = parser.parse_args()

    if args.train:
        train()

    if args.test:
        model = load_model()
        if model:
            # Benign user
            benign = build_feature_vector(180, 45, 62, 1, 0.95, 88, 3)
            benign_score = predict(benign, model)
            print(f"Benign user anomaly score:    {benign_score:.3f}")

            # Obvious bot
            bot = build_feature_vector(2, 1.1, 0, 14, 0.1, 44, 85)
            bot_score = predict(bot, model)
            print(f"Bot user anomaly score:       {bot_score:.3f}")
            print(f"\nDifference: {abs(bot_score - benign_score):.3f} (larger = more separable)")
