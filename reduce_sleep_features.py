import pandas as pd

# Load the labeled dataset
df = pd.read_csv('sleep_features_labeled.csv')

# Select required columns
required_cols = [
    'subject_id', 'sleep_onset_latency_min', 'total_sleep_time_min',
    'wake_after_sleep_onset_min', 'rem_latency_min', 'sleep_efficiency_percent',
    'percent_w', 'percent_n1', 'percent_n2', 'percent_n3', 'percent_rem',
    'insomnia_severity'
]

# Keep only required columns
df_reduced = df[required_cols]

# Save reduced dataset
df_reduced.to_csv('sleep_features_labels_core.csv', index=False)
