import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import tempfile
from datetime import datetime
import mne
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Set page config
st.set_page_config(
    page_title="InsomniAid - Insomnia Severity Prediction",
    page_icon="😴",
    layout="wide"
)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# Simple user database (in production, use proper database)
USERS_DB = {
    "admin": "password123",
    "doctor": "doctor123",
    "researcher": "research123"
}

def authenticate_user(username, password):
    return USERS_DB.get(username) == password

def register_user(username, password):
    if username not in USERS_DB:
        USERS_DB[username] = password
        return True
    return False

def extract_features_from_edf(psg_file, hypno_file):
    """Extract features from uploaded EDF files"""
    try:
        # Load PSG data
        raw = mne.io.read_raw_edf(psg_file, preload=True, verbose=False)
        
        # Load hypnogram
        annotations = mne.read_annotations(hypno_file)
        raw.set_annotations(annotations)
        
        # Stage mapping
        stage_mapping = {
            'Sleep stage W': 'W',
            'Sleep stage 1': 'N1', 
            'Sleep stage 2': 'N2',
            'Sleep stage 3': 'N3',
            'Sleep stage 4': 'N3',
            'Sleep stage R': 'REM',
            'Sleep stage ?': 'UNKNOWN'
        }
        
        # Extract sleep stages
        sleep_stages = []
        epoch_duration = 30  # seconds
        
        for onset, duration, description in zip(annotations.onset, annotations.duration, annotations.description):
            stage = stage_mapping.get(description, 'UNKNOWN')
            num_epochs = max(1, int(duration / epoch_duration))
            for _ in range(num_epochs):
                sleep_stages.append(stage)
        
        # Calculate features
        total_epochs = len(sleep_stages)
        total_recording_time = total_epochs * 0.5  # minutes
        
        # Sleep stages count
        stage_counts = pd.Series(sleep_stages).value_counts()
        sleep_stages_list = ['N1', 'N2', 'N3', 'REM']
        
        # Total sleep time
        sleep_epochs = sum(stage_counts.get(stage, 0) for stage in sleep_stages_list)
        total_sleep_time = sleep_epochs * 0.5
        
        # Sleep efficiency
        sleep_efficiency = (total_sleep_time / total_recording_time) * 100 if total_recording_time > 0 else 0
        
        # Sleep onset latency
        try:
            first_sleep_idx = next(i for i, stage in enumerate(sleep_stages) if stage in sleep_stages_list)
            sleep_onset_latency = first_sleep_idx * 0.5
        except StopIteration:
            sleep_onset_latency = 0
        
        # Wake after sleep onset
        if 'first_sleep_idx' in locals():
            post_onset_stages = sleep_stages[first_sleep_idx:]
            waso_epochs = sum(1 for stage in post_onset_stages if stage == 'W')
            wake_after_sleep_onset = waso_epochs * 0.5
        else:
            wake_after_sleep_onset = 0
        
        # REM latency
        try:
            first_rem_idx = next(i for i, stage in enumerate(sleep_stages) if stage == 'REM')
            rem_latency = (first_rem_idx - first_sleep_idx) * 0.5 if 'first_sleep_idx' in locals() else 0
        except StopIteration:
            rem_latency = 0
        
        # Stage percentages
        percent_w = (stage_counts.get('W', 0) / total_epochs) * 100 if total_epochs > 0 else 0
        percent_n1 = (stage_counts.get('N1', 0) / total_epochs) * 100 if total_epochs > 0 else 0
        percent_n2 = (stage_counts.get('N2', 0) / total_epochs) * 100 if total_epochs > 0 else 0
        percent_n3 = (stage_counts.get('N3', 0) / total_epochs) * 100 if total_epochs > 0 else 0
        percent_rem = (stage_counts.get('REM', 0) / total_epochs) * 100 if total_epochs > 0 else 0
        
        features = {
            'sleep_onset_latency_min': sleep_onset_latency,
            'total_sleep_time_min': total_sleep_time,
            'wake_after_sleep_onset_min': wake_after_sleep_onset,
            'rem_latency_min': rem_latency,
            'sleep_efficiency_percent': sleep_efficiency,
            'percent_w': percent_w,
            'percent_n1': percent_n1,
            'percent_n2': percent_n2,
            'percent_n3': percent_n3,
            'percent_rem': percent_rem
        }
        
        return features
        
    except Exception as e:
        st.error(f"Error processing EDF files: {str(e)}")
        return None

def normalize_features(features_dict):
    """Normalize features using the EXACT same method as training data"""
    try:
        # Load the original training data (before normalization)
        original_train = pd.read_csv('sleep_features_labels_core.csv')
        
        # Get feature columns (same order as training)
        feature_cols = ['sleep_onset_latency_min', 'total_sleep_time_min', 'wake_after_sleep_onset_min',
                       'rem_latency_min', 'sleep_efficiency_percent', 'percent_w', 'percent_n1', 
                       'percent_n2', 'percent_n3', 'percent_rem']
        
        # Extract only the feature columns from training data (exclude subject_id and insomnia_severity)
        training_features = original_train[feature_cols]
        
        # Create DataFrame from new features (same order)
        new_features_df = pd.DataFrame([features_dict])
        new_features_ordered = new_features_df[feature_cols]
        
        # Fit scaler on original training data
        scaler = StandardScaler()
        scaler.fit(training_features)
        
        # Transform new features using the same scaler
        normalized_features = scaler.transform(new_features_ordered)
        
        # Create normalized DataFrame with same column names
        normalized_df = pd.DataFrame(normalized_features, columns=feature_cols)
        
        # Debug: Show the extracted and normalized values
        st.write("**Debug Info:**")
        st.write("Extracted Features:")
        st.write(new_features_df)
        st.write("Normalized Features:")
        st.write(normalized_df)
        
        return normalized_df
        
    except Exception as e:
        st.error(f"Error normalizing features: {str(e)}")
        st.write(f"Features received: {features_dict}")
        return None

def predict_severity(normalized_features):
    """Predict insomnia severity using trained model"""
    try:
        # Load trained model
        model = joblib.load('random_forest_model.joblib')
        
        # Make prediction
        prediction = model.predict(normalized_features)
        probability = model.predict_proba(normalized_features)
        
        # Get class names
        classes = model.classes_
        
        # Debug info
        st.write("**Model Debug Info:**")
        st.write(f"Model classes: {classes}")
        st.write(f"Prediction: {prediction[0]}")
        st.write("Probabilities:")
        for i, cls in enumerate(classes):
            st.write(f"  {cls}: {probability[0][i]:.3f}")
        
        return prediction[0], probability[0]
        
    except Exception as e:
        st.error(f"Error making prediction: {str(e)}")
        return None, None

# Test with sample data function
def test_with_sample_data():
    """Test the model with known sample data"""
    st.subheader("🧪 Test Model with Sample Data")
    
    if st.button("Test with Sample Patient Data"):
        # Use a sample from your test data (a mild case)
        sample_features = {
            'sleep_onset_latency_min': 20.0,
            'total_sleep_time_min': 392.0,
            'wake_after_sleep_onset_min': 18.5,
            'rem_latency_min': 82.0,
            'sleep_efficiency_percent': 91.06,
            'percent_w': 8.94,
            'percent_n1': 17.54,
            'percent_n2': 38.21,
            'percent_n3': 20.09,
            'percent_rem': 15.21
        }
        
        st.write("Sample Features:")
        st.write(sample_features)
        
        # Normalize and predict
        normalized = normalize_features(sample_features)
        if normalized is not None:
            severity, probabilities = predict_severity(normalized)
            st.write(f"**Predicted Severity: {severity}**")
            st.write("This should be 'Mild' based on the training data")

def get_personalized_recommendations(severity):
    """Get personalized recommendations based on severity"""
    recommendations = {
        'No Insomnia': {
            'message': "Your sleep patterns appear normal. Continue maintaining good sleep hygiene!",
            'tips': [
                "Maintain consistent sleep schedule",
                "Create relaxing bedtime routine", 
                "Keep bedroom cool and dark",
                "Limit screen time before bed"
            ]
        },
        'Mild': {
            'message': "You have mild insomnia. Small changes can make a big difference.",
            'tips': [
                "Establish regular sleep-wake times",
                "Practice relaxation techniques before bed",
                "Avoid caffeine 6 hours before bedtime",
                "Get morning sunlight exposure",
                "Consider sleep hygiene improvements"
            ]
        },
        'Moderate': {
            'message': "You have moderate insomnia. Consider implementing structured interventions.",
            'tips': [
                "Try Cognitive Behavioral Therapy for Insomnia (CBT-I)",
                "Implement sleep restriction therapy",
                "Practice progressive muscle relaxation",
                "Consider keeping a sleep diary",
                "Consult with a sleep specialist"
            ]
        },
        'Severe': {
            'message': "You have severe insomnia. Professional help is recommended.",
            'tips': [
                "Consult a sleep medicine specialist immediately",
                "Consider professional CBT-I therapy", 
                "Discuss medication options with doctor",
                "Undergo comprehensive sleep study",
                "Address underlying medical conditions",
                "Consider intensive sleep rehabilitation program"
            ]
        }
    }
    
    return recommendations.get(severity, recommendations['Severe'])

# Authentication Pages
def login_page():
    st.title("🔐 Login to InsomniAid")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login", use_container_width=True)
            
            if login_btn:
                if authenticate_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.markdown("---")
        
        with st.form("register_form"):
            st.subheader("Register New Account")
            new_username = st.text_input("New Username")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            register_btn = st.form_submit_button("Register", use_container_width=True)
            
            if register_btn:
                if new_password != confirm_password:
                    st.error("Passwords don't match!")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters!")
                elif register_user(new_username, new_password):
                    st.success("Registration successful! Please login.")
                else:
                    st.error("Username already exists!")

# Main Application
def main_app():
    # Sidebar
    with st.sidebar:
        st.title(f"👋 Welcome, {st.session_state.username}!")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
    
    # Main header
    st.title("😴 InsomniAid")
    st.subheader("AI-Powered Insomnia Severity Prediction & Personalized Solutions")
    
    st.markdown("""
    Welcome to InsomniAid! Upload your PSG (Polysomnography) files to get:
    - **Accurate severity classification** using advanced machine learning
    - **Personalized treatment recommendations** based on your results
    - **Evidence-based insights** from sleep medicine research
    """)
    
    st.markdown("---")
    
    # Add test functionality
    test_with_sample_data()
    st.markdown("---")
    
    # File upload section
    st.header("📁 Upload Your PSG Files")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("PSG Data File")
        psg_file = st.file_uploader(
            "Upload PSG .edf file", 
            type=['edf'],
            help="Upload your polysomnography EDF file"
        )
    
    with col2:
        st.subheader("Hypnogram File") 
        hypno_file = st.file_uploader(
            "Upload Hypnogram .edf file",
            type=['edf'], 
            help="Upload your sleep stage annotation EDF file"
        )
    
    # Process files when both are uploaded
    if psg_file and hypno_file:
        st.markdown("---")
        
        if st.button("🔍 Analyze Sleep Data", use_container_width=True):
            with st.spinner("Processing your sleep data..."):
                # Create temporary files
                with tempfile.NamedTemporaryFile(delete=False, suffix='.edf') as tmp_psg:
                    tmp_psg.write(psg_file.getvalue())
                    tmp_psg_path = tmp_psg.name
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.edf') as tmp_hypno:
                    tmp_hypno.write(hypno_file.getvalue())
                    tmp_hypno_path = tmp_hypno.name
                
                try:
                    # Extract features
                    st.info("Extracting sleep features...")
                    features = extract_features_from_edf(tmp_psg_path, tmp_hypno_path)
                    
                    if features:
                        # Normalize features
                        st.info("Normalizing features...")
                        normalized_features = normalize_features(features)
                        
                        if normalized_features is not None:
                            # Predict severity
                            st.info("Predicting insomnia severity...")
                            severity, probabilities = predict_severity(normalized_features)
                            
                            if severity:
                                # Display results
                                st.success("Analysis completed!")
                                
                                # Results section
                                st.markdown("---")
                                st.header("📊 Your Sleep Analysis Results")
                                
                                # Severity prediction
                                col1, col2, col3 = st.columns([2, 1, 2])
                                
                                with col2:
                                    # Color-code severity
                                    severity_colors = {
                                        'No Insomnia': 'green',
                                        'Mild': 'orange', 
                                        'Moderate': 'red',
                                        'Severe': 'darkred'
                                    }
                                    
                                    st.markdown(f"""
                                    <div style="
                                        background-color: {severity_colors.get(severity, 'gray')};
                                        color: white;
                                        padding: 20px;
                                        border-radius: 10px;
                                        text-align: center;
                                        font-size: 24px;
                                        font-weight: bold;
                                    ">
                                        {severity}
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                # Sleep metrics
                                st.subheader("🏥 Sleep Metrics Summary")
                                
                                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                                
                                with metrics_col1:
                                    st.metric("Sleep Efficiency", f"{features['sleep_efficiency_percent']:.1f}%")
                                    st.metric("Total Sleep Time", f"{features['total_sleep_time_min']:.1f} min")
                                
                                with metrics_col2:
                                    st.metric("Sleep Onset Latency", f"{features['sleep_onset_latency_min']:.1f} min")
                                    st.metric("Wake After Sleep Onset", f"{features['wake_after_sleep_onset_min']:.1f} min")
                                
                                with metrics_col3:
                                    st.metric("REM Latency", f"{features['rem_latency_min']:.1f} min")
                                    st.metric("REM Sleep", f"{features['percent_rem']:.1f}%")
                                
                                # Personalized recommendations
                                st.markdown("---")
                                st.header("💡 Personalized Recommendations")
                                
                                recommendations = get_personalized_recommendations(severity)
                                
                                st.info(recommendations['message'])
                                
                                st.subheader("Recommended Actions:")
                                for i, tip in enumerate(recommendations['tips'], 1):
                                    st.write(f"{i}. {tip}")
                
                finally:
                    # Clean up temporary files
                    try:
                        os.unlink(tmp_psg_path)
                        os.unlink(tmp_hypno_path)
                    except:
                        pass

# Main app logic
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()
