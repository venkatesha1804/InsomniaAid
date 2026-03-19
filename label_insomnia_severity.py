import pandas as pd
import numpy as np

def create_insomnia_severity_labels(df):
    """
    Create insomnia severity labels based on clinical criteria
    using core sleep features: sleep onset latency, wake after sleep onset,
    sleep efficiency, and total sleep time.
    """
    df['insomnia_severity'] = 'No Insomnia'
    
    severity_rules = {
        'sleep_onset_latency_min': {'mild': 15, 'moderate': 30, 'severe': 45},
        'wake_after_sleep_onset_min': {'mild': 15, 'moderate': 30, 'severe': 45},
        'sleep_efficiency_percent': {'mild': 85, 'moderate': 75, 'severe': 65},
        'total_sleep_time_min': {'mild': 420, 'moderate': 360, 'severe': 300}
    }
    
    severity_scores = pd.DataFrame(index=df.index)
    severity_scores['sol_score'] = 0
    severity_scores['waso_score'] = 0  
    severity_scores['se_score'] = 0
    severity_scores['tst_score'] = 0
    
    # Sleep Onset Latency scoring
    if 'sleep_onset_latency_min' in df.columns:
        severity_scores.loc[df['sleep_onset_latency_min'] >= severity_rules['sleep_onset_latency_min']['severe'], 'sol_score'] = 3
        severity_scores.loc[(df['sleep_onset_latency_min'] >= severity_rules['sleep_onset_latency_min']['moderate']) & (df['sleep_onset_latency_min'] < severity_rules['sleep_onset_latency_min']['severe']), 'sol_score'] = 2
        severity_scores.loc[(df['sleep_onset_latency_min'] >= severity_rules['sleep_onset_latency_min']['mild']) & (df['sleep_onset_latency_min'] < severity_rules['sleep_onset_latency_min']['moderate']), 'sol_score'] = 1
    
    # Wake After Sleep Onset scoring
    if 'wake_after_sleep_onset_min' in df.columns:
        severity_scores.loc[df['wake_after_sleep_onset_min'] >= severity_rules['wake_after_sleep_onset_min']['severe'], 'waso_score'] = 3
        severity_scores.loc[(df['wake_after_sleep_onset_min'] >= severity_rules['wake_after_sleep_onset_min']['moderate']) & (df['wake_after_sleep_onset_min'] < severity_rules['wake_after_sleep_onset_min']['severe']), 'waso_score'] = 2
        severity_scores.loc[(df['wake_after_sleep_onset_min'] >= severity_rules['wake_after_sleep_onset_min']['mild']) & (df['wake_after_sleep_onset_min'] < severity_rules['wake_after_sleep_onset_min']['moderate']), 'waso_score'] = 1
    
    # Sleep Efficiency scoring (lower is worse)
    if 'sleep_efficiency_percent' in df.columns:
        severity_scores.loc[df['sleep_efficiency_percent'] <= severity_rules['sleep_efficiency_percent']['severe'], 'se_score'] = 3
        severity_scores.loc[(df['sleep_efficiency_percent'] > severity_rules['sleep_efficiency_percent']['severe']) & (df['sleep_efficiency_percent'] <= severity_rules['sleep_efficiency_percent']['moderate']), 'se_score'] = 2
        severity_scores.loc[(df['sleep_efficiency_percent'] > severity_rules['sleep_efficiency_percent']['moderate']) & (df['sleep_efficiency_percent'] <= severity_rules['sleep_efficiency_percent']['mild']), 'se_score'] = 1
    
    # Total Sleep Time scoring (lower is worse)
    if 'total_sleep_time_min' in df.columns:
        severity_scores.loc[df['total_sleep_time_min'] <= severity_rules['total_sleep_time_min']['severe'], 'tst_score'] = 3
        severity_scores.loc[(df['total_sleep_time_min'] > severity_rules['total_sleep_time_min']['severe']) & (df['total_sleep_time_min'] <= severity_rules['total_sleep_time_min']['moderate']), 'tst_score'] = 2
        severity_scores.loc[(df['total_sleep_time_min'] > severity_rules['total_sleep_time_min']['moderate']) & (df['total_sleep_time_min'] <= severity_rules['total_sleep_time_min']['mild']), 'tst_score'] = 1
    
    severity_scores['total_score'] = severity_scores['sol_score'] + severity_scores['waso_score'] + severity_scores['se_score'] + severity_scores['tst_score']
    
    # Assign severity labels based on total score
    df.loc[severity_scores['total_score'] == 0, 'insomnia_severity'] = 'No Insomnia'
    df.loc[(severity_scores['total_score'] >= 1) & (severity_scores['total_score'] <= 3), 'insomnia_severity'] = 'Mild'
    df.loc[(severity_scores['total_score'] >= 4) & (severity_scores['total_score'] <= 7), 'insomnia_severity'] = 'Moderate'
    df.loc[severity_scores['total_score'] >= 8, 'insomnia_severity'] = 'Severe'
    
    return df, severity_scores

def main():
    try:
        # Load your dataset
        df = pd.read_csv(r'D:\\mjrprjct\\sleep_features.csv')
        print(f"✅ Loaded dataset with {df.shape[0]} records and {df.shape[1]} features")
        
        # Apply insomnia severity labeling
        labeled_df, severity_scores = create_insomnia_severity_labels(df)
        print("✅ Insomnia severity labeling applied successfully.")
        
        # Save the labeled dataset
        labeled_df.to_csv(r'D:\\mjrprjct\\sleep_features_labeled.csv', index=False)
        print("✅ Labeled dataset saved as 'sleep_features_labeled.csv' in your project folder.")
        
        # Show distribution summary
        print("\n📊 Insomnia Severity Distribution:")
        print(labeled_df['insomnia_severity'].value_counts())
    
    except FileNotFoundError:
        print("❌ Error: 'sleep_features.csv' not found in the specified folder.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == '__main__':
    main()
