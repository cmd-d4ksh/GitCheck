import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

data = pd.read_csv("ml/dataset.csv")

X = data[["commit_score", "contributor_score", "issue_score"]]
y = data["label"]

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)
model.fit(X, y)

joblib.dump(model, "ml/model.pkl")

print("Model trained and saved")
