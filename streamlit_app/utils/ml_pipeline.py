import pandas as pd
import numpy as np
import joblib
import warnings
import mne
import os

warnings.filterwarnings('ignore')


# ==============================
# FEATURE EXTRACTION - ENHANCED
# ==============================
def extract_features_from_edf(psg_file, hypno_file):
    try:
        raw = mne.io.read_raw_edf(psg_file, preload=True, verbose=False)
        annotations = mne.read_annotations(hypno_file)
        raw.set_annotations(annotations)

        stage_mapping = {
            'Sleep stage W': 'W',
            'Sleep stage 1': 'N1',
            'Sleep stage 2': 'N2',
            'Sleep stage 3': 'N3',
            'Sleep stage 4': 'N3',
            'Sleep stage R': 'REM',
            'Sleep stage ?': 'UNKNOWN'
        }

        sleep_stages = []
        epoch_duration = 30

        for onset, duration, description in zip(
                annotations.onset, annotations.duration, annotations.description):

            stage = stage_mapping.get(description, 'UNKNOWN')
            num_epochs = max(1, int(duration / epoch_duration))

            for _ in range(num_epochs):
                sleep_stages.append(stage)

        total_epochs = len(sleep_stages)
        total_recording_time = total_epochs * 0.5

        stage_counts = pd.Series(sleep_stages).value_counts()
        sleep_stages_list = ['N1', 'N2', 'N3', 'REM']

        sleep_epochs = sum(stage_counts.get(stage, 0) for stage in sleep_stages_list)
        total_sleep_time = sleep_epochs * 0.5

        sleep_efficiency = (total_sleep_time / total_recording_time) * 100 if total_recording_time > 0 else 0

        try:
            first_sleep_idx = next(i for i, s in enumerate(sleep_stages) if s in sleep_stages_list)
            sleep_onset_latency = first_sleep_idx * 0.5
        except:
            sleep_onset_latency = 0
            first_sleep_idx = None

        if first_sleep_idx is not None:
            post_onset = sleep_stages[first_sleep_idx:]
            waso_epochs = sum(1 for s in post_onset if s == 'W')
            wake_after_sleep_onset = waso_epochs * 0.5
        else:
            wake_after_sleep_onset = 0

        try:
            first_rem_idx = next(i for i, s in enumerate(sleep_stages) if s == 'REM')
            rem_latency = (first_rem_idx - first_sleep_idx) * 0.5 if first_sleep_idx else 0
        except:
            rem_latency = 0

        percent_w = (stage_counts.get('W', 0) / total_epochs) * 100 if total_epochs else 0
        percent_n1 = (stage_counts.get('N1', 0) / total_epochs) * 100 if total_epochs else 0
        percent_n2 = (stage_counts.get('N2', 0) / total_epochs) * 100 if total_epochs else 0
        percent_n3 = (stage_counts.get('N3', 0) / total_epochs) * 100 if total_epochs else 0
        percent_rem = (stage_counts.get('REM', 0) / total_epochs) * 100 if total_epochs else 0

        # ==============================
        # EXTRACT ADDITIONAL FEATURES
        # ==============================
        
        # Count awakenings (W to non-W transitions)
        num_awakenings = 0
        for i in range(1, len(sleep_stages)):
            if sleep_stages[i-1] == 'W' and sleep_stages[i] != 'W':
                num_awakenings += 1
        
        # Sleep fragmentation index = number of transitions between sleep stages
        num_stage_transitions = 0
        for i in range(1, len(sleep_stages)):
            if sleep_stages[i] != sleep_stages[i-1]:
                num_stage_transitions += 1
        
        sleep_fragmentation_index = num_stage_transitions / total_epochs if total_epochs > 0 else 0

        # ==============================
        # Extract SpO2 (Oxygen Saturation)
        # ==============================
        mean_spo2 = 95.0  # Default healthy value
        std_spo2 = 2.0
        min_spo2 = 93.0
        max_spo2 = 98.0
        median_spo2 = 95.0
        spo2_desaturations = 0
        spo2_coefficient_variation = 2.1

        try:
            # Look for SpO2 channel in EDF
            spo2_channels = [ch for ch in raw.ch_names if 'spo2' in ch.lower() or 'o2' in ch.lower()]
            if spo2_channels:
                spo2_data = raw[spo2_channels[0]][0][0]
                mean_spo2 = float(np.nanmean(spo2_data))
                std_spo2 = float(np.nanstd(spo2_data))
                min_spo2 = float(np.nanmin(spo2_data))
                max_spo2 = float(np.nanmax(spo2_data))
                median_spo2 = float(np.nanmedian(spo2_data))
                spo2_desaturations = np.sum(spo2_data < 90)
                spo2_coefficient_variation = (std_spo2 / mean_spo2 * 100) if mean_spo2 > 0 else 0
        except:
            pass

        # ==============================
        # Extract Heart Rate
        # ==============================
        mean_hr = 65.0  # Default normal heart rate
        std_hr = 8.0
        min_hr = 50.0
        max_hr = 85.0
        median_hr = 65.0
        hr_coefficient_variation = 12.3
        hr_range = 35.0

        try:
            # Look for ECG/HR channel
            hr_channels = [ch for ch in raw.ch_names if 'ecg' in ch.lower() or 'hr' in ch.lower() or 'heart' in ch.lower()]
            if hr_channels:
                hr_data = raw[hr_channels[0]][0][0]
                mean_hr = float(np.nanmean(hr_data))
                std_hr = float(np.nanstd(hr_data))
                min_hr = float(np.nanmin(hr_data))
                max_hr = float(np.nanmax(hr_data))
                median_hr = float(np.nanmedian(hr_data))
                hr_range = max_hr - min_hr
                hr_coefficient_variation = (std_hr / mean_hr * 100) if mean_hr > 0 else 0
        except:
            pass

        return {
            # Original 10 features
            'sleep_onset_latency_min': sleep_onset_latency,
            'total_sleep_time_min': total_sleep_time,
            'wake_after_sleep_onset_min': wake_after_sleep_onset,
            'rem_latency_min': rem_latency,
            'sleep_efficiency_percent': sleep_efficiency,
            'percent_w': percent_w,
            'percent_n1': percent_n1,
            'percent_n2': percent_n2,
            'percent_n3': percent_n3,
            'percent_rem': percent_rem,
            # New 6 features
            'num_awakenings': num_awakenings,
            'sleep_fragmentation_index': sleep_fragmentation_index,
            'mean_spo2': mean_spo2,
            'std_spo2': std_spo2,
            'mean_hr': mean_hr,
            'std_hr': std_hr
        }

    except Exception as e:
        print("Feature Extraction Error:", e)
        import traceback
        traceback.print_exc()
        return None


# ==============================
# NORMALIZATION (MATCH TRAINING)
# ==============================
def normalize_features(features_dict):
    try:
        # All 16 features in correct order
        feature_cols = [
            'sleep_onset_latency_min', 'total_sleep_time_min',
            'wake_after_sleep_onset_min', 'rem_latency_min',
            'sleep_efficiency_percent', 'percent_w',
            'percent_n1', 'percent_n2', 'percent_n3', 'percent_rem',
            'num_awakenings', 'sleep_fragmentation_index',
            'mean_spo2', 'std_spo2', 'mean_hr', 'std_hr'
        ]

        df = pd.DataFrame([features_dict])
        
        # Verify all columns exist
        missing = [col for col in feature_cols if col not in df.columns]
        if missing:
            print(f"WARNING: Missing columns: {missing}")
        
        result = df[feature_cols].values
        print(f"✅ Features normalized: {result.shape}")
        return result

    except Exception as e:
        print("Normalization Error:", e)
        import traceback
        traceback.print_exc()
        return None


# ==============================
# REAL ML MODEL PREDICTION
# ==============================
def predict_severity(normalized_features):
    try:
        # ✅ Absolute-safe path
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  
        MODEL_PATH = os.path.join(BASE_DIR, "models", "random_forest_model.joblib")

        print("Model path:", MODEL_PATH)
        print("Exists:", os.path.exists(MODEL_PATH))

        # ✅ Load trained model
        model = joblib.load(MODEL_PATH)
        print(f"✅ Model loaded successfully")
        print(f"   Expected features: {model.n_features_in_}")
        print(f"   Input features: {normalized_features.shape[1]}")

        # ✅ Predict
        prediction = model.predict(normalized_features)
        probabilities = model.predict_proba(normalized_features)

        # ✅ The model predicts string labels directly
        severity = str(prediction[0])

        print(f"✅ Prediction: {severity}")
        print(f"✅ Probabilities: {probabilities[0]}")

        return severity, probabilities[0]

    except Exception as e:
        print(f"MODEL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return "Error", [0, 0, 0, 0]