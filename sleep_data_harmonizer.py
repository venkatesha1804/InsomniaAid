import os
import mne
import pandas as pd
import numpy as np
from glob import glob
import warnings
warnings.filterwarnings('ignore')

class SleepDataHarmonizer:
    """
    Unified data loader and harmonizer for Sleep-EDF and ISRUC datasets
    """
    
    def __init__(self, sleep_edf_dir=r'D:\\mjrPrjct\\sleep-edf-data', isruc_dir=r'D:\\mjrPrjct\\ISRUC_Dataset'):
        self.sleep_edf_dir = sleep_edf_dir
        self.isruc_dir = isruc_dir
        self.epoch_duration = 30  # seconds
        
        # Standardized sleep stage mapping
        self.stage_mapping = {
            # Sleep-EDF format
            'Sleep stage W': 'W',
            'Sleep stage 1': 'N1', 
            'Sleep stage 2': 'N2',
            'Sleep stage 3': 'N3',
            'Sleep stage 4': 'N3',  # Combine N3 and N4
            'Sleep stage R': 'REM',
            'Sleep stage ?': 'UNKNOWN',
            'Movement time': 'MOVEMENT',
            
            # ISRUC format
            'W': 'W',
            'N1': 'N1',
            'N2': 'N2', 
            'N3': 'N3',
            'N4': 'N3',  # Combine N3 and N4
            'R': 'REM',
            'REM': 'REM',
            
            # Numeric codes
            '0': 'W',
            '1': 'N1',
            '2': 'N2',
            '3': 'N3',
            '4': 'N3',
            '5': 'REM',
            0: 'W',
            1: 'N1', 
            2: 'N2',
            3: 'N3',
            4: 'N3',
            5: 'REM'
        }
    
    def find_sleep_edf_pairs(self):
        """Find Sleep-EDF PSG and Hypnogram file pairs with explicit subfolder search"""
        file_pairs = []
        
        # Search within 'sleep-cassette' and 'sleep-telemetry' subfolders explicitly
        subfolders = ['sleep-cassette', 'sleep-telemetry']
        
        for subfolder in subfolders:
            folder_path = os.path.join(self.sleep_edf_dir, subfolder)
            if not os.path.exists(folder_path):
                continue
                
            psg_files = glob(os.path.join(folder_path, '*-PSG.edf'))
            hypno_files = glob(os.path.join(folder_path, '*-Hypnogram.edf'))
            
            print(f"In {subfolder}: Found {len(psg_files)} PSG files and {len(hypno_files)} Hypnogram files")
            
            # Create dictionary to map PSG files by their base name
            for psg_file in psg_files:
                psg_basename = os.path.basename(psg_file).replace('-PSG.edf', '')
                
                # Find matching hypnogram file by checking if hypno file starts with same prefix
                matched_hypno = None
                for hypno_file in hypno_files:
                    hypno_basename = os.path.basename(hypno_file).replace('-Hypnogram.edf', '')
                    
                    # Check if they share the same core prefix (first 6-7 characters typically)
                    if hypno_basename.startswith(psg_basename[:6]):
                        matched_hypno = hypno_file
                        break
                
                if matched_hypno:
                    file_pairs.append({
                        'subject_id': psg_basename,
                        'psg_file': psg_file,
                        'hypno_file': matched_hypno,
                        'dataset': 'sleep-edf'
                    })
        
        print(f"Found {len(file_pairs)} Sleep-EDF file pairs total")
        return file_pairs
    
    def find_isruc_files(self):
        """Find ISRUC data files"""
        excel_files = glob(os.path.join(self.isruc_dir, '**', '*.xlsx'), recursive=True)
        
        file_pairs = []
        
        for excel_file in excel_files:
            base_name = os.path.splitext(os.path.basename(excel_file))[0]
            
            text_file = excel_file.replace('.xlsx', '.txt')
            if not os.path.exists(text_file):
                directory = os.path.dirname(excel_file)
                possible_text = glob(os.path.join(directory, f'{base_name}*.txt'))
                text_file = possible_text[0] if possible_text else None
            
            file_pairs.append({
                'subject_id': base_name,
                'excel_file': excel_file,
                'text_file': text_file if text_file and os.path.exists(text_file) else None,
                'dataset': 'isruc'
            })
        
        print(f"Found {len(file_pairs)} ISRUC file pairs")
        return file_pairs
    
    def load_sleep_edf_data(self, psg_file, hypno_file):
        """Load and process Sleep-EDF data"""
        try:
            raw = mne.io.read_raw_edf(psg_file, preload=True, verbose=False)
            annotations = mne.read_annotations(hypno_file)  # Removed verbose=False
            raw.set_annotations(annotations)
            
            sleep_stages = []
            physiological_data = {'SpO2': [], 'HR': [], 'events': []}
            
            for onset, duration, description in zip(annotations.onset, annotations.duration, annotations.description):
                stage = self.stage_mapping.get(description, 'UNKNOWN')
                num_epochs = max(1, int(duration / self.epoch_duration))
                for _ in range(num_epochs):
                    sleep_stages.append(stage)
                    physiological_data['SpO2'].append(np.nan)
                    physiological_data['HR'].append(np.nan)
                    physiological_data['events'].append('')
            
            return {
                'sleep_stages': sleep_stages,
                'physiological_data': physiological_data,
                'total_epochs': len(sleep_stages),
                'dataset_type': 'sleep-edf'
            }
        except Exception as e:
            print(f"Error loading Sleep-EDF data from {psg_file}: {e}")
            return None
    
    def load_isruc_data(self, excel_file, text_file=None):
        """Load and process ISRUC data"""
        try:
            df = pd.read_excel(excel_file, sheet_name=0)
            df.columns = df.columns.str.strip()
            
            if 'Stage' in df.columns:
                stages_raw = df['Stage'].fillna('W')
            elif 'stage' in df.columns:
                stages_raw = df['stage'].fillna('W')
            else:
                print(f"No Stage column found in {excel_file}")
                return None
            
            sleep_stages = [self.stage_mapping.get(str(stage), 'UNKNOWN') for stage in stages_raw]
            
            physiological_data = {
                'SpO2': df.get('SpO2', [np.nan] * len(sleep_stages)).fillna(np.nan).tolist(),
                'HR': df.get('HR', [np.nan] * len(sleep_stages)).fillna(np.nan).tolist(),
                'events': df.get('Events', [''] * len(sleep_stages)).fillna('').tolist()
            }
            
            if text_file:
                with open(text_file, 'r') as f:
                    text_stages = [line.strip() for line in f if line.strip()]
                text_stages_mapped = [self.stage_mapping.get(stage, 'UNKNOWN') for stage in text_stages]
                if len(text_stages_mapped) == len(sleep_stages):
                    sleep_stages = text_stages_mapped
                    print(f"Used text file for stages: {text_file}")
            
            return {
                'sleep_stages': sleep_stages,
                'physiological_data': physiological_data,
                'total_epochs': len(sleep_stages),
                'dataset_type': 'isruc'
            }
        except Exception as e:
            print(f"Error loading ISRUC data from {excel_file}: {e}")
            return None
    
    def create_unified_dataset(self):
        """Create unified dataset from both Sleep-EDF and ISRUC"""
        all_subjects = []
        
        print("\n=== Processing Sleep-EDF Data ===")
        sleep_edf_pairs = self.find_sleep_edf_pairs()
        for pair in sleep_edf_pairs:
            print(f"Processing Sleep-EDF subject: {pair['subject_id']}")
            data = self.load_sleep_edf_data(pair['psg_file'], pair['hypno_file'])
            if data:
                subject_record = {
                    'subject_id': pair['subject_id'],
                    'dataset': 'sleep-edf',
                    'sleep_stages': data['sleep_stages'],
                    'spo2_values': data['physiological_data']['SpO2'],
                    'hr_values': data['physiological_data']['HR'],
                    'events': data['physiological_data']['events'],
                    'total_epochs': data['total_epochs'],
                    'total_duration_hours': data['total_epochs'] * self.epoch_duration / 3600
                }
                all_subjects.append(subject_record)
        
        print("\n=== Processing ISRUC Data ===")
        isruc_pairs = self.find_isruc_files()
        for pair in isruc_pairs:
            print(f"Processing ISRUC subject: {pair['subject_id']}")
            data = self.load_isruc_data(pair['excel_file'], pair.get('text_file'))
            if data:
                subject_record = {
                    'subject_id': pair['subject_id'],
                    'dataset': 'isruc',
                    'sleep_stages': data['sleep_stages'],
                    'spo2_values': data['physiological_data']['SpO2'],
                    'hr_values': data['physiological_data']['HR'],
                    'events': data['physiological_data']['events'],
                    'total_epochs': data['total_epochs'],
                    'total_duration_hours': data['total_epochs'] * self.epoch_duration / 3600
                }
                all_subjects.append(subject_record)
        
        print("\n=== Harmonization Complete ===")
        print(f"Total subjects processed: {len(all_subjects)}")
        
        summary_data = []
        for subject in all_subjects:
            stage_counts = pd.Series(subject['sleep_stages']).value_counts()
            summary_data.append({
                'subject_id': subject['subject_id'],
                'dataset': subject['dataset'],
                'total_epochs': subject['total_epochs'],
                'duration_hours': subject['total_duration_hours'],
                'wake_epochs': stage_counts.get('W', 0),
                'n1_epochs': stage_counts.get('N1', 0),
                'n2_epochs': stage_counts.get('N2', 0),
                'n3_epochs': stage_counts.get('N3', 0),
                'rem_epochs': stage_counts.get('REM', 0),
                'unknown_epochs': stage_counts.get('UNKNOWN', 0),
                'has_spo2': not all(pd.isna(subject['spo2_values'])),
                'has_hr': not all(pd.isna(subject['hr_values'])),
                'has_events': any(subject['events'])
            })
        
        summary_df = pd.DataFrame(summary_data)
        return all_subjects, summary_df
    
    def save_harmonized_data(self, subjects_data, summary_df, output_dir='harmonized_data'):
        """Save harmonized data to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        summary_df.to_csv(os.path.join(output_dir, 'dataset_summary.csv'), index=False)
        
        detailed_data = []
        for subject in subjects_data:
            for epoch_idx, stage in enumerate(subject['sleep_stages']):
                detailed_data.append({
                    'subject_id': subject['subject_id'],
                    'dataset': subject['dataset'],
                    'epoch': epoch_idx + 1,
                    'sleep_stage': stage,
                    'spo2': subject['spo2_values'][epoch_idx] if epoch_idx < len(subject['spo2_values']) else np.nan,
                    'hr': subject['hr_values'][epoch_idx] if epoch_idx < len(subject['hr_values']) else np.nan,
                    'events': subject['events'][epoch_idx] if epoch_idx < len(subject['events']) else ''
                })
        
        detailed_df = pd.DataFrame(detailed_data)
        detailed_df.to_csv(os.path.join(output_dir, 'harmonized_epoch_data.csv'), index=False)
        
        print(f"\nHarmonized data saved to: {output_dir}/")
        print(f"- dataset_summary.csv: Summary statistics per subject")
        print(f"- harmonized_epoch_data.csv: Detailed epoch-level data")
        return summary_df, detailed_df

def main():
    """Main function to run data harmonization"""
    print("=== Sleep Data Harmonization Pipeline ===\n")
    
    harmonizer = SleepDataHarmonizer()
    
    subjects_data, summary_df = harmonizer.create_unified_dataset()
    
    if len(subjects_data) == 0:
        print("No data found. Please check your data directories.")
        return
    
    print("\n=== Dataset Summary ===")
    print(f"Sleep-EDF subjects: {len(summary_df[summary_df['dataset']=='sleep-edf'])}")
    print(f"ISRUC subjects: {len(summary_df[summary_df['dataset']=='isruc'])}")
    print(f"Total subjects: {len(summary_df)}")
    print(f"\nAverage recording duration: {summary_df['duration_hours'].mean():.1f} hours")
    print(f"Total epochs across all subjects: {summary_df['total_epochs'].sum()}")
    
    stage_totals = {
        'Wake': summary_df['wake_epochs'].sum(),
        'N1': summary_df['n1_epochs'].sum(), 
        'N2': summary_df['n2_epochs'].sum(),
        'N3': summary_df['n3_epochs'].sum(),
        'REM': summary_df['rem_epochs'].sum()
    }
    
    print("\nSleep stage distribution across all subjects:")
    for stage, count in stage_totals.items():
        percentage = count / sum(stage_totals.values()) * 100
        print(f"  {stage}: {count:,} epochs ({percentage:.1f}%)")
    
    harmonizer.save_harmonized_data(subjects_data, summary_df)

if __name__ == "__main__":
    main()
