import pandas as pd
import numpy as np
import os


def generate_clinical_data():
    """Build a merged clinical CSV for training a tabular model.

    This script will try to read `data/patient_info.csv` and
    `data/patient_diagnosis.csv`. If `patient_info.csv` is missing
    it will generate reasonable synthetic Age/Sex/BMI values so the
    workflow is reproducible.
    """
    print("Building Clinical Tabular Dataset...")

    diag_path = os.path.join("data", "patient_diagnosis.csv")
    info_path = os.path.join("data", "patient_info.csv")

    if not os.path.exists(diag_path):
        raise FileNotFoundError("Please place patient_diagnosis.csv under data/")

    diagnoses_df = pd.read_csv(diag_path, header=None, names=["patient_id", "disease"]) 
    diagnoses_df["patient_id"] = diagnoses_df["patient_id"].astype(str)

    if os.path.exists(info_path):
        info_df = pd.read_csv(info_path, header=None,
                              names=['patient_id', 'age', 'sex', 'bmi_adult', 'weight_child', 'height_child'])
        info_df['patient_id'] = info_df['patient_id'].astype(str)
    else:
        print("patient_info.csv not found — generating synthetic demographics.")
        np.random.seed(42)
        patient_ids = diagnoses_df['patient_id'].astype(str).tolist()
        n = len(patient_ids)
        ages = np.clip(np.random.normal(50, 18, size=n).round().astype(int), 5, 95)
        sexes = np.random.choice(['M', 'F'], size=n, p=[0.5, 0.5])
        bmis = np.clip(np.random.normal(25, 4, size=n).round(1), 15.0, 45.0)

        info_df = pd.DataFrame({
            'patient_id': patient_ids,
            'age': ages,
            'sex': sexes,
            'bmi_adult': bmis,
            'weight_child': [pd.NA] * n,
            'height_child': [pd.NA] * n,
        })

    # Merge diagnosis with demographics
    df = pd.merge(info_df, diagnoses_df, on='patient_id', how='inner')

    # Clean basic fields
    df['age'] = df['age'].fillna(df['age'].median())
    df['bmi'] = df['bmi_adult'].fillna(22.0)

    # Normalize/encode sex values: map common textual forms to 1/0
    df['sex'] = df['sex'].map({'M': 1, 'F': 0, 'Male': 1, 'Female': 0}).fillna(df['sex'])
    # If still not numeric, coerce with a safe fallback
    try:
        df['sex'] = df['sex'].astype(int)
    except Exception:
        df['sex'] = df['sex'].apply(lambda x: 1 if str(x).strip() in ['1', 'True', 'true'] else 0)

    # Simulate vitals based on disease
    np.random.seed(42)
    spO2, temp, smoker = [], [], []

    for _, row in df.iterrows():
        disease = row['disease']
        o2 = np.random.uniform(97, 100)
        t = np.random.uniform(36.5, 37.2)
        smk = np.random.choice([0, 1], p=[0.8, 0.2])

        if disease == 'COPD':
            o2 = np.random.uniform(88, 95)
            smk = np.random.choice([0, 1], p=[0.1, 0.9])
        elif disease == 'Pneumonia':
            o2 = np.random.uniform(90, 96)
            t = np.random.uniform(38.0, 40.0)
        elif disease == 'Asthma':
            o2 = np.random.uniform(94, 98)
        elif disease == 'Bronchiectasis':
            o2 = np.random.uniform(90, 96)

        spO2.append(round(o2, 1))
        temp.append(round(t, 1))
        smoker.append(int(smk))

    df['spo2'] = spO2
    df['temperature'] = temp
    df['smoker'] = smoker

    final_df = df[['patient_id', 'age', 'sex', 'bmi', 'spo2', 'temperature', 'smoker', 'disease']]
    os.makedirs('data', exist_ok=True)
    final_df.to_csv('data/master_clinical_data.csv', index=False)
    print("Saved as data/master_clinical_data.csv")


if __name__ == "__main__":
    generate_clinical_data()
