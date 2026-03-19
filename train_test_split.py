import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

# Load the data
data = pd.read_csv('sleep_features_labels_core_normalized.csv')

# Separate features and label
X = data.drop(['subject_id', 'insomnia_severity'], axis=1)
y = data['insomnia_severity']

# Split into train and test sets (80-20)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize scaler and fit only on train data
scaler = MinMaxScaler()
X_train_norm = scaler.fit_transform(X_train)
X_test_norm = scaler.transform(X_test)

# Convert back to DataFrames for convenience
X_train_norm = pd.DataFrame(X_train_norm, columns=X.columns, index=X_train.index)
X_test_norm = pd.DataFrame(X_test_norm, columns=X.columns, index=X_test.index)

# Print dataset shapes
print("Training set features shape:", X_train_norm.shape)
print("Testing set features shape:", X_test_norm.shape)
print("Training set labels shape:", y_train.shape)
print("Testing set labels shape:", y_test.shape)

# Save processed data to new CSV files
X_train_norm.to_csv('X_train_normalized.csv', index=False)
X_test_norm.to_csv('X_test_normalized.csv', index=False)
y_train.to_csv('y_train.csv', index=False)
y_test.to_csv('y_test.csv', index=False)