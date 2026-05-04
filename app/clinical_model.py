import os
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier

from .dataset import DISEASE_MAP


def train_and_save_rf():
    """Train a lightweight Random Forest on `data/master_clinical_data.csv`.

    Saves the trained model as `clinical_weights.pkl` in the project root.
    """
    csv_path = os.path.join('data', 'master_clinical_data.csv')
    if not os.path.exists(csv_path):
        raise FileNotFoundError("Please run prepare_clinical.py to generate data/master_clinical_data.csv")

    df = pd.read_csv(csv_path)

    X = df[['age', 'sex', 'bmi', 'spo2', 'temperature', 'smoker']]
    y = df['disease'].map(DISEASE_MAP)

    # Fill any remaining NaNs with column means
    X = X.fillna(X.mean())

    rf_model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    rf_model.fit(X, y)

    joblib.dump(rf_model, 'clinical_weights.pkl')
    print("Clinical Model trained and saved as 'clinical_weights.pkl'")


# Load model at import time if available (API will check rf_model is not None)
rf_model = None
if os.path.exists('clinical_weights.pkl'):
    rf_model = joblib.load('clinical_weights.pkl')


def reload_rf_model():
    """Reload the Random Forest from disk after a fresh training run."""
    global rf_model
    if os.path.exists('clinical_weights.pkl'):
        try:
            rf_model = joblib.load('clinical_weights.pkl')
            return True
        except Exception:
            return False
    return False
