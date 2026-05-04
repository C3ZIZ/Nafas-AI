import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import os

# We map text back to the integer IDs (0-7) used by the Audio CNN
DISEASE_MAP = {
    "Healthy": 0, "COPD": 1, "Asthma": 2, "Bronchiectasis": 3,
    "Pneumonia": 4, "URTI": 5, "LRTI": 6, "Bronchiolitis": 7
}

def train_nlp():
    df = pd.read_csv('data/master_nlp_data.csv')
    X = df['patient_text']
    y = df['mapped_disease'].map(DISEASE_MAP)
    
    # Drop rows where mapping failed
    mask = y.notna()
    X, y = X[mask], y[mask].astype(int)
    
    # Build the lightweight NLP Pipeline
    # TF-IDF converts text to numbers based on word importance
    model = make_pipeline(TfidfVectorizer(stop_words='english', ngram_range=(1, 2)), MultinomialNB())
    model.fit(X, y)
    
    joblib.dump(model, 'nlp_weights.pkl')
    print("NLP Model trained and saved as 'nlp_weights.pkl'")

# Load model for API
nlp_model = None
if os.path.exists('nlp_weights.pkl'):
    try:
        nlp_model = joblib.load('nlp_weights.pkl')
    except Exception:
        nlp_model = None


def reload_nlp_model():
    """Reload the NLP pipeline from disk after a fresh training run."""
    global nlp_model
    if os.path.exists('nlp_weights.pkl'):
        try:
            nlp_model = joblib.load('nlp_weights.pkl')
            return True
        except Exception:
            return False
    return False
