import joblib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "ml" / "model.pkl"

model = None

def load_model():
    global model
    if model is None:
        model = joblib.load(MODEL_PATH)
    return model


def predict_trust(features: dict):
    clf = load_model()

    X = [[
        features["commit_score"],
        features["contributor_score"],
        features["issue_score"]
    ]]

    prediction = clf.predict(X)[0]
    probability = clf.predict_proba(X)[0][prediction]

    return {
        "ml_label": int(prediction),
        "confidence": round(float(probability), 2)
    }
