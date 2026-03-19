import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib   # For saving the model

# 1. Load the normalized and split datasets
X_train = pd.read_csv('X_train_normalized.csv')
X_test = pd.read_csv('X_test_normalized.csv')
y_train = pd.read_csv('y_train.csv').squeeze()   # Ensures y is a 1D series
y_test = pd.read_csv('y_test.csv').squeeze()

# 2. Initialize and train the Random Forest model
clf = RandomForestClassifier(random_state=42)
clf.fit(X_train, y_train)

# Save the trained model to a file
joblib.dump(clf, 'random_forest_model.joblib')
print("Trained model saved as 'random_forest_model.joblib'")

# 3. Predict on the test set
y_pred = clf.predict(X_test)

# 4. Evaluate performance
print("Accuracy:", clf.score(X_test, y_test))
print("Classification Report:\n", classification_report(y_test, y_pred))
print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))

# 5. Display most important features
importances = pd.Series(clf.feature_importances_, index=X_train.columns)
print("Feature Importances:\n", importances.sort_values(ascending=False))
