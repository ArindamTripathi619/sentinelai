"""
SentinelAI — ML Training Data Generator
Owner: Parthiv (in coordination with Akash)

Generates synthetic behavioral feature vectors for training the Isolation Forest.
Output: scripts/training_data.csv

Run: python generate_training_data.py
"""

import numpy as np
import pandas as pd
import os

np.random.seed(42)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "training_data.csv")

# Feature names — must match ml_model.py FEATURE_NAMES
COLUMNS = [
    "typing_variance_ms",
    "time_to_complete_sec",
    "mouse_move_count",
    "registrations_from_ip_1h",
    "email_pattern_score",
    "keypress_count",
    "session_actions_per_min",
    "label",  # 0 = benign, 1 = malicious
]


def generate_benign(n=200):
    """
    Simulate real human users registering on a platform.
    High variance in behavior — humans are unpredictable.
    """
    return pd.DataFrame({
        "typing_variance_ms":       np.random.normal(180, 60, n).clip(60, 450),
        "time_to_complete_sec":     np.random.normal(45, 20, n).clip(10, 180),
        "mouse_move_count":         np.random.normal(55, 25, n).clip(10, 200).astype(int),
        "registrations_from_ip_1h": np.random.choice([1, 1, 1, 2], n),
        "email_pattern_score":      np.random.uniform(0.75, 1.0, n),
        "keypress_count":           np.random.normal(95, 30, n).clip(40, 250).astype(int),
        "session_actions_per_min":  np.random.normal(4, 2, n).clip(1, 12),
        "label":                    np.zeros(n, dtype=int),
    })


def generate_malicious(n=100):
    """
    Simulate bots and malicious registrations.
    Tight, uniform, inhuman distributions.
    """
    # Mix of attack profiles
    n_bot = n // 2          # Pure script bots
    n_wave = n // 4         # IP-based bot wave
    n_semi = n - n_bot - n_wave  # Semi-automated (slightly harder to detect)

    # Pure bots — extremely fast, no mouse, uniform typing
    bots = pd.DataFrame({
        "typing_variance_ms":       np.random.uniform(0, 8, n_bot),
        "time_to_complete_sec":     np.random.uniform(0.5, 2.5, n_bot),
        "mouse_move_count":         np.zeros(n_bot, dtype=int),
        "registrations_from_ip_1h": np.random.randint(8, 25, n_bot),
        "email_pattern_score":      np.random.uniform(0.0, 0.2, n_bot),
        "keypress_count":           np.random.randint(30, 55, n_bot),
        "session_actions_per_min":  np.random.uniform(50, 120, n_bot),
        "label":                    np.ones(n_bot, dtype=int),
    })

    # IP-wave bots — multiple fast registrations from same IP
    wave = pd.DataFrame({
        "typing_variance_ms":       np.random.uniform(5, 20, n_wave),
        "time_to_complete_sec":     np.random.uniform(1.5, 4, n_wave),
        "mouse_move_count":         np.random.randint(0, 5, n_wave),
        "registrations_from_ip_1h": np.random.randint(5, 20, n_wave),
        "email_pattern_score":      np.random.uniform(0.1, 0.35, n_wave),
        "keypress_count":           np.random.randint(40, 70, n_wave),
        "session_actions_per_min":  np.random.uniform(30, 80, n_wave),
        "label":                    np.ones(n_wave, dtype=int),
    })

    # Semi-automated — harder to catch (borderline)
    semi = pd.DataFrame({
        "typing_variance_ms":       np.random.uniform(15, 50, n_semi),
        "time_to_complete_sec":     np.random.uniform(3, 8, n_semi),
        "mouse_move_count":         np.random.randint(0, 15, n_semi),
        "registrations_from_ip_1h": np.random.randint(3, 8, n_semi),
        "email_pattern_score":      np.random.uniform(0.2, 0.5, n_semi),
        "keypress_count":           np.random.randint(35, 75, n_semi),
        "session_actions_per_min":  np.random.uniform(15, 40, n_semi),
        "label":                    np.ones(n_semi, dtype=int),
    })

    return pd.concat([bots, wave, semi], ignore_index=True)


def main():
    print("Generating synthetic training data...")

    benign = generate_benign(200)
    malicious = generate_malicious(100)

    df = pd.concat([benign, malicious], ignore_index=True)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved {len(df)} samples to {OUTPUT_PATH}")
    print(f"  Benign:    {len(benign)} samples (label=0)")
    print(f"  Malicious: {len(malicious)} samples (label=1)")
    print(f"\nFeature summary (benign):")
    print(benign.drop("label", axis=1).describe().round(2))
    print(f"\nFeature summary (malicious):")
    print(malicious.drop("label", axis=1).describe().round(2))
    print(f"\nNext step: run `python backend/ml_model.py --train` to train the model.")


if __name__ == "__main__":
    main()
