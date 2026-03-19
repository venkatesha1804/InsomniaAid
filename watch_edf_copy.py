import mne
import warnings

# Optional: ignore specific warnings for cleaner output
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Path to your EDF file
edf_file = 'sleep-edf-data/sleep-cassette/SC4001EC-Hypnogram.edf'

# Load raw EDF data with minimal verbosity to reduce warnings
raw = mne.io.read_raw_edf(edf_file, preload=True, verbose='ERROR')

# Print basic info about the loaded file
print(raw.info)

# Plot the raw signal in an interactive window
# You can scroll, zoom, select channels etc.
raw.plot(title='EDF File Visualization', duration=30, n_channels=10, scalings='auto')

# Keep the plot open until closed manually (necessary for some environments)
import matplotlib.pyplot as plt
plt.show()
