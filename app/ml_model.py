"""Optional ML predictor.

The bundled model was trained on six rows and is effectively meaningless as a
classifier. This module is kept for backwards compatibility but is NOT used by
the main scoring pipeline. The rule-based score in `trust_score.py` is the
primary signal. If a proper labeled dataset is added later, expose the model
via `predict_trust` and wire it in via an explicit API parameter.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import joblib

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "ml" / "model.pkl"

_model = None
_load_attempted = False


def _load_model():
    global _model, _load_attempted
    if _load_attempted:
        return _model
    _load_attempted = True
    try:
        if MODEL_PATH.exists():
            _model = joblib.load(MODEL_PATH)
    except Exception:
        _model = None
    return _model


def predict_trust(features: dict) -> Optional[dict]:
    """Return ML prediction if a model is available, else None.

    Not used by the primary scoring path. The hosted model in this repo was
    fit on six rows and should not be treated as a reliable classifier.
    """
    model = _load_model()
    if model is None:
        return None
    try:
        x = [[
            features.get("commit_score", 0.0),
            features.get("contributor_score", 0.0),
            features.get("issue_score", 0.0),
        ]]
        prediction = int(model.predict(x)[0])
        proba = model.predict_proba(x)[0]
        classes = list(getattr(model, "classes_", [0, 1]))
        idx = classes.index(prediction) if prediction in classes else 0
        confidence = round(float(proba[idx]), 3)
        return {"label": prediction, "confidence": confidence}
    except Exception:
        return None
