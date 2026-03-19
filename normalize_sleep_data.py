import pandas as pd
from sklearn.preprocessing import StandardScaler

# Step 1: Load your CSV file (update the file path if needed)
file_path = 'sleep_features_labels_core.csv'
data = pd.read_csv(file_path)

# Step 2: Select feature columns (exclude 'subject_id' and label columns)
feature_cols = [col for col in data.columns if col not in ['subject_id', 'insomnia_severity']]

# Step 3: Extract features and labels separately
features = data[feature_cols]
labels = data['insomnia_severity']

# Step 4: Initialize scaler and normalize features
scaler = StandardScaler()
features_normalized = scaler.fit_transform(features)

# Step 5: Create a DataFrame with normalized features
data_normalized = pd.DataFrame(features_normalized, columns=feature_cols)

# Step 6: Add back 'subject_id' and 'insomnia_severity' columns
data_normalized['subject_id'] = data['subject_id']
data_normalized['insomnia_severity'] = labels

# Step 7: Save the normalized data to a new CSV file
output_file = 'sleep_features_labels_core_normalized.csv'
data_normalized.to_csv(output_file, index=False)

print(f'Normalized data saved to {output_file}')
