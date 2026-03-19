
import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class SleepFeatureExtractor:
    """
    Extract comprehensive sleep features from harmonized epoch-level sleep data
    """

    def __init__(self, epoch_duration_min=0.5):
        """
        Initialize feature extractor

        Parameters:
        epoch_duration_min: Duration of each epoch in minutes (default: 0.5 for 30-second epochs)
        """
        self.epoch_duration_min = epoch_duration_min

    def extract_features(self, epoch_df):
        """
        Extract all sleep features for a single subject/night

        Parameters:
        epoch_df: DataFrame with columns [subject_id, dataset, epoch, sleep_stage, spo2, hr, events]

        Returns:
        Dictionary with extracted features
        """
        features = {}

        # Basic information
        subject_id = epoch_df['subject_id'].iloc[0]
        dataset = epoch_df['dataset'].iloc[0]
        features['subject_id'] = subject_id
        features['dataset'] = dataset

        # Convert to numpy arrays for faster processing
        stages = epoch_df['sleep_stage'].values
        total_epochs = len(stages)
        features['total_epochs'] = total_epochs
        features['total_recording_time_min'] = total_epochs * self.epoch_duration_min

        # Handle physiological data
        spo2_values = self._clean_physiological_data(epoch_df, 'spo2')
        hr_values = self._clean_physiological_data(epoch_df, 'hr')
        events = epoch_df['events'].fillna('').astype(str).values

        # === CORE SLEEP ARCHITECTURE FEATURES ===

        # 1. Total Sleep Time (TST)
        sleep_stages = ['N1', 'N2', 'N3', 'REM']
        sleep_epochs_mask = np.isin(stages, sleep_stages)
        total_sleep_epochs = np.sum(sleep_epochs_mask)
        total_sleep_time = total_sleep_epochs * self.epoch_duration_min
        features['total_sleep_time_min'] = total_sleep_time
        features['total_sleep_time_hours'] = total_sleep_time / 60

        # 2. Sleep Efficiency
        if total_epochs > 0:
            sleep_efficiency = (total_sleep_time / (total_epochs * self.epoch_duration_min)) * 100
            features['sleep_efficiency_percent'] = sleep_efficiency
        else:
            features['sleep_efficiency_percent'] = np.nan

        # 3. Sleep Onset Latency (SOL)
        try:
            first_sleep_idx = np.where(sleep_epochs_mask)[0][0]
            sleep_onset_latency = first_sleep_idx * self.epoch_duration_min
            features['sleep_onset_latency_min'] = sleep_onset_latency
        except IndexError:
            # No sleep epochs found
            features['sleep_onset_latency_min'] = np.nan
            first_sleep_idx = None

        # 4. Wake After Sleep Onset (WASO)
        if first_sleep_idx is not None:
            post_onset_stages = stages[first_sleep_idx:]
            waso_epochs = np.sum(post_onset_stages == 'W')
            waso_time = waso_epochs * self.epoch_duration_min
            features['wake_after_sleep_onset_min'] = waso_time
        else:
            features['wake_after_sleep_onset_min'] = np.nan

        # 5. REM Latency
        try:
            first_rem_idx = np.where(stages == 'REM')[0][0]
            if first_sleep_idx is not None:
                rem_latency = (first_rem_idx - first_sleep_idx) * self.epoch_duration_min
                features['rem_latency_min'] = rem_latency
            else:
                features['rem_latency_min'] = np.nan
        except IndexError:
            # No REM epochs found
            features['rem_latency_min'] = np.nan

        # 6. Sleep Stage Percentages
        for stage in ['W', 'N1', 'N2', 'N3', 'REM', 'UNKNOWN', 'MOVEMENT']:
            stage_count = np.sum(stages == stage)
            stage_percent = (stage_count / total_epochs) * 100 if total_epochs > 0 else 0
            features[f'percent_{stage.lower()}'] = stage_percent
            features[f'total_{stage.lower()}_min'] = stage_count * self.epoch_duration_min

        # === SLEEP FRAGMENTATION FEATURES ===

        # 7. Number of Awakenings (Wake epochs after sleep onset)
        if first_sleep_idx is not None:
            awakenings = self._count_transitions_to_stage(stages[first_sleep_idx:], 'W')
            features['num_awakenings'] = awakenings
        else:
            features['num_awakenings'] = 0

        # 8. Number of Sleep Stage Transitions
        features['num_stage_transitions'] = self._count_all_stage_transitions(stages)

        # 9. Sleep Fragmentation Index (transitions per hour of sleep)
        if total_sleep_time > 0:
            fragmentation_index = (features['num_stage_transitions'] / (total_sleep_time / 60))
            features['sleep_fragmentation_index'] = fragmentation_index
        else:
            features['sleep_fragmentation_index'] = np.nan

        # === AROUSAL AND EVENT FEATURES ===

        # 10. Arousal Events
        arousal_keywords = ['AR', 'Arousal', 'AROUSAL']
        arousal_events = self._count_events_with_keywords(events, arousal_keywords)
        features['num_arousal_events'] = arousal_events

        # 11. Movement Events
        movement_keywords = ['MChg', 'Movement', 'MOVEMENT']
        movement_events = self._count_events_with_keywords(events, movement_keywords)
        features['num_movement_events'] = movement_events

        # 12. Respiratory Events
        respiratory_keywords = ['OA', 'OH', 'CA', 'MH', 'H']
        respiratory_events = self._count_events_with_keywords(events, respiratory_keywords)
        features['num_respiratory_events'] = respiratory_events

        # 13. Total Events
        non_empty_events = np.sum([len(event.strip()) > 0 for event in events])
        features['total_events'] = non_empty_events

        # === PHYSIOLOGICAL FEATURES ===

        # 14. SpO2 Features
        if len(spo2_values) > 0 and not np.isnan(spo2_values).all():
            valid_spo2 = spo2_values[~np.isnan(spo2_values)]
            features['mean_spo2'] = np.mean(valid_spo2)
            features['std_spo2'] = np.std(valid_spo2)
            features['min_spo2'] = np.min(valid_spo2)
            features['max_spo2'] = np.max(valid_spo2)
            features['median_spo2'] = np.median(valid_spo2)

            # SpO2 desaturation events (drops below 90%)
            desaturations = np.sum(valid_spo2 < 90)
            features['spo2_desaturations'] = desaturations

            # SpO2 variability
            features['spo2_coefficient_variation'] = (np.std(valid_spo2) / np.mean(valid_spo2)) * 100
        else:
            for metric in ['mean_spo2', 'std_spo2', 'min_spo2', 'max_spo2', 'median_spo2', 
                          'spo2_desaturations', 'spo2_coefficient_variation']:
                features[metric] = np.nan

        # 15. Heart Rate Features
        if len(hr_values) > 0 and not np.isnan(hr_values).all():
            valid_hr = hr_values[~np.isnan(hr_values)]
            features['mean_hr'] = np.mean(valid_hr)
            features['std_hr'] = np.std(valid_hr)
            features['min_hr'] = np.min(valid_hr)
            features['max_hr'] = np.max(valid_hr)
            features['median_hr'] = np.median(valid_hr)

            # Heart rate variability metrics
            features['hr_coefficient_variation'] = (np.std(valid_hr) / np.mean(valid_hr)) * 100
            features['hr_range'] = np.max(valid_hr) - np.min(valid_hr)
        else:
            for metric in ['mean_hr', 'std_hr', 'min_hr', 'max_hr', 'median_hr',
                          'hr_coefficient_variation', 'hr_range']:
                features[metric] = np.nan

        # === SLEEP CONTINUITY FEATURES ===

        # 16. Longest Wake Bout
        features['longest_wake_bout_min'] = self._longest_consecutive_stage(stages, 'W') * self.epoch_duration_min

        # 17. Longest Sleep Bout
        longest_sleep_bout = 0
        for stage in sleep_stages:
            bout_length = self._longest_consecutive_stage(stages, stage)
            longest_sleep_bout = max(longest_sleep_bout, bout_length)
        features['longest_sleep_bout_min'] = longest_sleep_bout * self.epoch_duration_min

        # 18. Sleep Bout Analysis
        features['mean_sleep_bout_length_min'] = self._mean_bout_length(stages, sleep_stages) * self.epoch_duration_min
        features['mean_wake_bout_length_min'] = self._mean_bout_length(stages, ['W']) * self.epoch_duration_min

        return features

    def _clean_physiological_data(self, df, column):
        """Clean and validate physiological data"""
        if column not in df.columns:
            return np.array([])

        data = df[column].copy()

        # Convert to numeric, coercing errors to NaN
        data = pd.to_numeric(data, errors='coerce')

        # Remove physiological outliers
        if column == 'spo2':
            # SpO2 should be between 70-100%
            data = data.where((data >= 70) & (data <= 100), np.nan)
        elif column == 'hr':
            # Heart rate should be between 30-200 bpm
            data = data.where((data >= 30) & (data <= 200), np.nan)

        return data.values

    def _count_transitions_to_stage(self, stages, target_stage):
        """Count transitions TO a specific stage"""
        transitions = 0
        for i in range(1, len(stages)):
            if stages[i] == target_stage and stages[i-1] != target_stage:
                transitions += 1
        return transitions

    def _count_all_stage_transitions(self, stages):
        """Count all stage transitions"""
        transitions = 0
        for i in range(1, len(stages)):
            if stages[i] != stages[i-1]:
                transitions += 1
        return transitions

    def _count_events_with_keywords(self, events, keywords):
        """Count events containing specific keywords"""
        count = 0
        for event in events:
            if any(keyword in event.upper() for keyword in keywords):
                count += 1
        return count

    def _longest_consecutive_stage(self, stages, target_stage):
        """Find longest consecutive occurrence of a stage"""
        max_length = 0
        current_length = 0

        for stage in stages:
            if stage == target_stage:
                current_length += 1
                max_length = max(max_length, current_length)
            else:
                current_length = 0

        return max_length

    def _mean_bout_length(self, stages, target_stages):
        """Calculate mean bout length for given stages"""
        bout_lengths = []
        current_length = 0

        for stage in stages:
            if stage in target_stages:
                current_length += 1
            else:
                if current_length > 0:
                    bout_lengths.append(current_length)
                    current_length = 0

        # Add final bout if it ends with target stage
        if current_length > 0:
            bout_lengths.append(current_length)

        return np.mean(bout_lengths) if bout_lengths else 0

def extract_sleep_features(harmonized_data_path, output_path='sleep_features.csv'):
    """
    Main function to extract features from harmonized sleep data

    Parameters:
    harmonized_data_path: Path to harmonized_epoch_data.csv
    output_path: Path to save extracted features
    """
    print("=== Sleep Feature Extraction Pipeline ===\n")

    # Load harmonized data
    print("Loading harmonized sleep data...")
    epoch_data = pd.read_csv(harmonized_data_path)
    print(f"Loaded {len(epoch_data):,} epochs from {epoch_data['subject_id'].nunique()} subjects")

    # Initialize feature extractor
    extractor = SleepFeatureExtractor()

    # Extract features per subject
    print("\nExtracting sleep features per subject...")
    features_list = []

    for i, (subject_id, group_df) in enumerate(epoch_data.groupby('subject_id')):
        if i % 50 == 0:
            print(f"Processing subject {i+1}/{epoch_data['subject_id'].nunique()}: {subject_id}")

        try:
            features = extractor.extract_features(group_df)
            features_list.append(features)
        except Exception as e:
            print(f"Error processing subject {subject_id}: {e}")
            continue

    # Create features DataFrame
    features_df = pd.DataFrame(features_list)

    # Handle missing data and imputation
    print("\n=== Data Cleaning and Imputation ===")
    print("Missing data summary:")
    missing_summary = features_df.isnull().sum()
    missing_summary = missing_summary[missing_summary > 0].sort_values(ascending=False)
    print(missing_summary)

    # Simple imputation strategy
    # For physiological features, use median imputation
    physio_columns = [col for col in features_df.columns if 'spo2' in col or 'hr' in col]
    sleep_columns = [col for col in features_df.columns if col not in physio_columns and 
                    col not in ['subject_id', 'dataset']]

    # Impute physiological features with dataset-specific medians
    for col in physio_columns:
        if col in features_df.columns:
            for dataset in ['sleep-edf', 'isruc']:
                mask = features_df['dataset'] == dataset
                if mask.any():
                    dataset_median = features_df.loc[mask, col].median()
                    features_df.loc[mask, col] = features_df.loc[mask, col].fillna(dataset_median)

    # For sleep features, use overall median (these should have fewer missing values)
    for col in sleep_columns:
        if col in features_df.columns and features_df[col].isnull().any():
            overall_median = features_df[col].median()
            features_df[col] = features_df[col].fillna(overall_median)

    # Save features
    features_df.to_csv(output_path, index=False)
    print(f"\n✅ Feature extraction complete!")
    print(f"📊 Extracted {len(features_df.columns)-2} features from {len(features_df)} subjects")
    print(f"💾 Features saved to: {output_path}")

    # Display feature summary
    print("\n=== Feature Summary ===")
    print(f"Sleep-EDF subjects: {len(features_df[features_df['dataset']=='sleep-edf'])}")
    print(f"ISRUC subjects: {len(features_df[features_df['dataset']=='isruc'])}")
    print(f"\nKey sleep metrics (mean ± std):")

    key_metrics = ['sleep_efficiency_percent', 'total_sleep_time_hours', 'sleep_onset_latency_min', 
                   'wake_after_sleep_onset_min', 'rem_latency_min', 'num_awakenings']

    for metric in key_metrics:
        if metric in features_df.columns:
            mean_val = features_df[metric].mean()
            std_val = features_df[metric].std()
            print(f"  {metric}: {mean_val:.2f} ± {std_val:.2f}")

    return features_df

# Example usage function
def main():
    """
    Main execution function
    """
    # Extract features from harmonized data
    features_df = extract_sleep_features(
        harmonized_data_path='harmonized_data/harmonized_epoch_data.csv',
        output_path='harmonized_data/sleep_features.csv'
    )

    return features_df

if __name__ == "__main__":
    features_df = main()
