import pandas as pd
import json
import os

# Map the Kaggle dataset diseases to our Nafas 8-class system
NLP_MAP = {
    "Bronchial Asthma": "Asthma",
    "Pneumonia": "Pneumonia",
    "Common Cold": "URTI",
    "Tuberculosis": "LRTI"
}

def build_nlp_system():
    print("Building NLP Dataset and Medical Knowledge Base...")
    
    # 1. Load the 4 Kaggle files
    df_symptoms = pd.read_csv('data/dataset.csv')
    df_desc = pd.read_csv('data/symptom_Description.csv')
    df_prec = pd.read_csv('data/symptom_precaution.csv')
    
    # 2. Build the Medical Knowledge Base (for the API response)
    knowledge_base = {}
    for _, row in df_desc.iterrows():
        disease = row['Disease'].strip()
        if disease in NLP_MAP:
            mapped_name = NLP_MAP[disease]
            knowledge_base[mapped_name] = {"description": row['Description']}
            
    for _, row in df_prec.iterrows():
        disease = row['Disease'].strip()
        if disease in NLP_MAP:
            mapped_name = NLP_MAP[disease]
            # Get all 4 precautions, drop NaNs
            precautions = [str(row[f'Precaution_{i}']).title() for i in range(1, 5) if pd.notna(row[f'Precaution_{i}'])]
            if mapped_name in knowledge_base:
                knowledge_base[mapped_name]["precautions"] = precautions

    # Add default knowledge for our other classes not in the Kaggle CSV
    knowledge_base["COPD"] = {"description": "Chronic inflammatory lung disease that causes obstructed airflow.", "precautions": ["Stop smoking", "Avoid air pollutants", "Use inhalers as prescribed"]}
    knowledge_base["Healthy"] = {"description": "Lungs are clear and functioning normally.", "precautions": ["Maintain regular exercise", "Eat a balanced diet"]}
    knowledge_base["Bronchiolitis"] = {"description": "A common lung infection in young children and infants.", "precautions": ["Drink plenty of fluids", "Use saline nose drops", "Rest"]}
    knowledge_base["Bronchiectasis"] = {"description": "Condition where the lungs' airways become damaged.", "precautions": ["Stay hydrated", "Perform chest physiotherapy", "Take prescribed antibiotics"]}

    # Save Knowledge Base to be loaded by FastAPI
    os.makedirs('data', exist_ok=True)
    with open('data/knowledge_base.json', 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, indent=4, ensure_ascii=False)

    # 3. Create NLP Training Data from dataset.csv
    # Combine symptom columns into a single string to simulate "patient text"
    symptom_cols = [col for col in df_symptoms.columns if 'Symptom' in col]
    df_symptoms['patient_text'] = df_symptoms[symptom_cols].apply(lambda x: ' '.join(x.dropna().astype(str).str.replace('_', ' ')), axis=1)
    
    # Filter for our respiratory diseases
    df_resp = df_symptoms[df_symptoms['Disease'].str.strip().isin(NLP_MAP.keys())].copy()
    df_resp['mapped_disease'] = df_resp['Disease'].str.strip().map(NLP_MAP)
    
    # Add synthetic data for our other classes to balance the 8-class model
    synthetic_data = [
        {"mapped_disease": "COPD", "patient_text": "chronic cough shortness of breath wheezing daily fatigue lot of mucus smoker"},
        {"mapped_disease": "Bronchiectasis", "patient_text": "coughing up thick yellow phlegm frequent chest infections bad breath"},
        {"mapped_disease": "Bronchiolitis", "patient_text": "baby is wheezing fast breathing nasal flaring fever"},
        {"mapped_disease": "Healthy", "patient_text": "feeling fine no cough breathing normally routine checkup clear chest"}
    ]
    synth_df = pd.DataFrame(synthetic_data * 50) # Multiply to balance the dataset
    
    final_df = pd.concat([df_resp[['patient_text', 'mapped_disease']], synth_df], ignore_index=True)
    os.makedirs('data', exist_ok=True)
    final_df.to_csv('data/master_nlp_data.csv', index=False)
    print("Complete! Generated 'data/master_nlp_data.csv' and 'data/knowledge_base.json'.")


if __name__ == "__main__":
    build_nlp_system()
