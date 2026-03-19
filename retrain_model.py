"""
RETRAIN YOUR INSOMNIA DETECTION MODEL
This script retrains the Random Forest model with the current scikit-learn version
"""

import pandas as pd
import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import warnings

warnings.filterwarnings('ignore')

# ==============================
# RETRAIN MODEL
# ==============================
def retrain_model():
    """
    Retrain the Random Forest model with current scikit-learn
    """
    try:
        print("=" * 60)
        print("🔄 RETRAINING INSOMNIA DETECTION MODEL")
        print("=" * 60)
        
        # Try different possible data file names
        possible_files = [
            "sleep_features_labeled.csv",
            "sleep_features_labels_core_normalized.csv",
            "X_train_normalized.csv",
            "data/sleep_features_labeled.csv",
        ]
        
        data_path = None
        for file_name in possible_files:
            if os.path.exists(file_name):
                data_path = file_name
                print(f"✅ Found training data: {file_name}")
                break
        
        if data_path is None:
            print("❌ Could not find training data file!")
            print("\nPlease enter the path to your training data CSV:")
            print("(or press Enter to search for it)")
            data_path = input("Path: ").strip()
            
            if not data_path or not os.path.exists(data_path):
                # List available CSV files
                print("\n📂 Available CSV files in current directory:")
                for file in os.listdir("."):
                    if file.endswith(".csv"):
                        print(f"   - {file}")
                print("\nPlease update the script with the correct file name!")
                return False
        
        print(f"\n📂 Loading data from: {data_path}")
        data = pd.read_csv(data_path)
        
        print(f"✅ Data loaded: {data.shape[0]} rows, {data.shape[1]} columns")
        print(f"\nFirst few rows:\n{data.head()}")
        print(f"\nColumn names:\n{data.columns.tolist()}")
        
        # Check for label column
        label_col = None
        for col in ['insomnia_severity', 'label', 'Label', 'insomnia_label', 'severity', 'Severity']:
            if col in data.columns:
                label_col = col
                break
        
        if label_col is None:
            print("\n❌ ERROR: Could not find label column!")
            print("Expected column names: 'label', 'Label', 'insomnia_label', 'severity', or 'Severity'")
            print(f"Available columns: {data.columns.tolist()}")
            return False
        
        print(f"\n✅ Found label column: '{label_col}'")
        print(f"\nLabel distribution:\n{data[label_col].value_counts()}")
        
        # Define feature columns (from your data)
        feature_cols = [
            'sleep_onset_latency_min', 'total_sleep_time_min',
            'wake_after_sleep_onset_min', 'rem_latency_min',
            'sleep_efficiency_percent', 'percent_w',
            'percent_n1', 'percent_n2', 'percent_n3', 'percent_rem',
            'num_awakenings', 'sleep_fragmentation_index',
            'mean_spo2', 'std_spo2', 'mean_hr', 'std_hr'
        ]
        
        # Check if all feature columns exist
        missing_cols = [col for col in feature_cols if col not in data.columns]
        if missing_cols:
            print(f"\n⚠️  WARNING: Missing feature columns: {missing_cols}")
            print(f"Available columns: {data.columns.tolist()}")
            print("Using available columns...")
            feature_cols = [col for col in feature_cols if col in data.columns]
        
        print(f"\n📊 Using {len(feature_cols)} features:")
        for col in feature_cols:
            print(f"   - {col}")
        
        X = data[feature_cols]
        y = data[label_col]
        
        print(f"\n📊 Features shape: {X.shape}")
        print(f"📊 Labels shape: {y.shape}")
        
        # Check for missing values
        if X.isnull().sum().sum() > 0:
            print("\n⚠️  Dropping rows with missing values...")
            X = X.fillna(X.mean())
        
        # Split data (80% train, 20% test)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"\n🔀 Train set: {X_train.shape[0]} samples")
        print(f"🔀 Test set: {X_test.shape[0]} samples")
        
        # Train model WITHOUT scaling (to match your app)
        print("\n🤖 Training Random Forest Classifier...")
        print("   (This may take a minute...)")
        
        model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            n_jobs=-1,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n✅ Model Training Complete!")
        print(f"\n📈 Model Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
        print("\n📋 Classification Report:")
        print(classification_report(y_test, y_pred, 
                                   target_names=['No Insomnia', 'Mild', 'Moderate', 'Severe'],
                                   zero_division=0))
        
        print("\n🔄 Confusion Matrix:")
        cm = confusion_matrix(y_test, y_pred)
        print(cm)
        
        # Create models directory if it doesn't exist
        models_dir = os.path.join("streamlit_app", "models")
        os.makedirs(models_dir, exist_ok=True)
        
        # Save model
        model_path = os.path.join(models_dir, "random_forest_model.joblib")
        joblib.dump(model, model_path)
        
        print(f"\n✅ Model saved successfully!")
        print(f"📁 Location: {model_path}")
        print(f"📦 Model size: {os.path.getsize(model_path) / 1024:.2f} KB")
        
        # Feature importance
        print("\n🎯 Top 5 Most Important Features:")
        importances = model.feature_importances_
        indices = np.argsort(importances)[-5:][::-1]
        for i, idx in enumerate(indices, 1):
            print(f"   {i}. {feature_cols[idx]}: {importances[idx]:.4f}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during retraining: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = retrain_model()
    if success:
        print("\n" + "=" * 60)
        print("✅ RETRAINING COMPLETE!")
        print("=" * 60)
        print("\nYour model has been successfully retrained and saved.")
        print("You can now run your Streamlit app without errors!")
        print("\nTo start your app, run:")
        print("   streamlit run streamlit_app/insomniad_app.py")
    else:
        print("\n" + "=" * 60)
        print("❌ RETRAINING FAILED")
        print("=" * 60)
        print("Please check the error message above and try again.")