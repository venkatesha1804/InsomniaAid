import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os

# Load dataset
data = pd.read_csv("streamlit_app/data/sleep_features_labels_core.csv")

# Features
feature_cols = [
    'sleep_onset_latency_min', 'total_sleep_time_min',
    'wake_after_sleep_onset_min', 'rem_latency_min',
    'sleep_efficiency_percent', 'percent_w',
    'percent_n1', 'percent_n2', 'percent_n3', 'percent_rem'
]

X = data[feature_cols]
y = data['label']

# ✅ Train WITHOUT scaling (to match your app)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# Save model
os.makedirs("streamlit_app/models", exist_ok=True)
joblib.dump(model, "streamlit_app/models/random_forest_model.joblib")

print("✅ Model trained & saved successfully!")