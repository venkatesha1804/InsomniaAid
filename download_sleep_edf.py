import requests
import os
import re

def get_hypnogram_files_from_directory(directory_url):
    response = requests.get(directory_url)
    response.raise_for_status()
    # Extract filenames from href attribute only
    pattern = r'href="([^"]*Hypnogram\.edf)"'
    return [m.split('/')[-1] for m in re.findall(pattern, response.text)]

base_url = "https://physionet.org/files/sleep-edfx/1.0.0/"
download_dir = "sleep-edf-data"
os.makedirs(download_dir, exist_ok=True)

# Read PSG files from RECORDS
with open("RECORDS", 'r') as f:
    psg_files = [line.strip() for line in f if line.strip()]

# Get hypnogram files
cassette_hypnos = get_hypnogram_files_from_directory(base_url + "sleep-cassette/")
telemetry_hypnos = get_hypnogram_files_from_directory(base_url + "sleep-telemetry/")

hypnogram_files = [f"sleep-cassette/{f}" for f in cassette_hypnos] + [f"sleep-telemetry/{f}" for f in telemetry_hypnos]

all_files = psg_files + hypnogram_files

for file_path in all_files:
    file_url = base_url + file_path
    local_file_path = os.path.join(download_dir, file_path.replace('/', os.sep))
    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

    if os.path.exists(local_file_path):
        print(f"Skipping existing file: {file_path}")
        continue

    print(f"Downloading: {file_url}")
    resp = requests.get(file_url, stream=True)
    resp.raise_for_status()
    with open(local_file_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

print("Download complete!")
