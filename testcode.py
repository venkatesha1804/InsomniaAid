import pandas as pd
import joblib
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# -----------------------------
# 1. Load trained model
# -----------------------------
model = joblib.load("random_forest_model.joblib")

# -----------------------------
# 2. Load NEW patient data (for prediction)
# -----------------------------
new_data = pd.read_csv("new_patient_data_normalized.csv")

# Predict severity for new patient
severity_predictions = model.predict(new_data)
print("Predicted Insomnia Severity:", severity_predictions)

# -----------------------------
# 3. (OPTIONAL BUT IMPORTANT) Accuracy calculation
# -----------------------------
# Load test data
X_test = pd.read_csv("X_test_normalized.csv")
y_test = pd.read_csv("y_test.csv")

# Convert y_test to 1D array
y_test = y_test.values.ravel()

# Predict on test set
y_pred = model.predict(X_test)

# Accuracy
accuracy = accuracy_score(y_test, y_pred)
print("\n✅ Model Accuracy:", accuracy)

# Confusion Matrix
print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# Classification Report
print("\nClassification Report:")
print(classification_report(y_test, y_pred))
