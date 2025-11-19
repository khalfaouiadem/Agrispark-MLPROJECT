from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import pickle  # pour charger votre modèle et scaler

# Initialisation de Flask
app = Flask(__name__)

# ---------------------------------------------------
# Charger le modèle Random Forest et le scaler
# ---------------------------------------------------
with open("savemodel1.sav", "rb") as f:
    best_rf_model = pickle.load(f)

with open("scaler.sav", "rb") as f:
    scaler = pickle.load(f)

best_model_name = 'Random Forest'  # utilisation unique de Random Forest

# ---------------------------------------------------
# Fonction de prédiction
# ---------------------------------------------------
def predict_potability(model, scaler, new_data):
    new_data_engineered = new_data.copy()
    
    # Features d'ingénierie
    new_data_engineered['Hardness_Solids_Ratio'] = new_data_engineered['Hardness'] / new_data_engineered['Solids']
    new_data_engineered['Chloramines_Sulfate_Ratio'] = new_data_engineered['Chloramines'] / new_data_engineered['Sulfate']
    new_data_engineered['Organic_Trihalo_Ratio'] = new_data_engineered['Organic_carbon'] / new_data_engineered['Trihalomethanes']
    new_data_engineered['ph_Hardness_Interaction'] = new_data_engineered['ph'] * new_data_engineered['Hardness']
    new_data_engineered['Conductivity_Solids_Interaction'] = new_data_engineered['Conductivity'] * new_data_engineered['Solids']
    
    # Remplacer infinis par médiane
    new_data_engineered = new_data_engineered.replace([np.inf, -np.inf], np.nan)
    for col in new_data_engineered.columns:
        if new_data_engineered[col].isnull().sum() > 0:
            new_data_engineered[col].fillna(new_data_engineered[col].median(), inplace=True)
    
    # Normalisation avec le scaler
    new_data_scaled = scaler.transform(new_data_engineered)

    # Prédiction
    prediction_proba = model.predict(new_data_scaled)[0]
    prediction = 1 if prediction_proba > 0.5 else 0
    
    return prediction, prediction_proba

# ---------------------------------------------------
# Routes Flask
# ---------------------------------------------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Récupération des valeurs du formulaire
        features = {
            'ph': float(request.form['ph']),
            'Hardness': float(request.form['Hardness']),
            'Solids': float(request.form['Solids']),
            'Chloramines': float(request.form['Chloramines']),
            'Sulfate': float(request.form['Sulfate']),
            'Conductivity': float(request.form['Conductivity']),
            'Organic_carbon': float(request.form['Organic_carbon']),
            'Trihalomethanes': float(request.form['Trihalomethanes']),
            'Turbidity': float(request.form['Turbidity'])
        }
        new_sample = pd.DataFrame([features])

        # Prédiction avec Random Forest et scaler
        prediction, probability = predict_potability(best_rf_model, scaler, new_sample)

        # Interprétation simple
        if prediction == 1:
            result_text = f"✅ POTABLE (Confiance: {probability:.2%})"
        else:
            result_text = f"❌ NON POTABLE (Confiance: {probability:.2%})"

        return render_template('index.html', prediction_text=result_text)

    except Exception as e:
        return render_template('index.html', prediction_text=f"Erreur : {str(e)}")

# ---------------------------------------------------
# Lancer Flask
# ---------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
