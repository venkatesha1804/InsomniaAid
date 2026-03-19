import requests
import os
from time import sleep

# Base URL patterns for the three subgroups
base_urls = {
    "subgroup1": "http://dataset.isr.uc.pt/ISRUC_Sleep/subgroupI/{}.rar",
    "subgroup2": "http://dataset.isr.uc.pt/ISRUC_Sleep/subgroupII/{}.rar",
    "subgroup3": "http://dataset.isr.uc.pt/ISRUC_Sleep/subgroupIII/{}.rar"
}

# Number of subjects in each subgroup
counts = {
    "subgroup1": 100,
    "subgroup2": 8,
    "subgroup3": 10
}

# Folder to save files
download_dir = "ISRUC_Dataset"
os.makedirs(download_dir, exist_ok=True)

def download_file(url, local_path):
    if os.path.exists(local_path):
        print(f"Skipping already downloaded file: {local_path}")
        return
    print(f"Downloading {url} ...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Saved to {local_path}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

# Download all files from all subgroups
for subgroup, base_url in base_urls.items():
    print(f"\nStarting downloads for {subgroup} ...")
    count = counts[subgroup]
    subgroup_dir = os.path.join(download_dir, subgroup)
    os.makedirs(subgroup_dir, exist_ok=True)
    for i in range(1, count + 1):
        url = base_url.format(i)
        local_file = os.path.join(subgroup_dir, f"{i}.rar")
        download_file(url, local_file)
        sleep(0.1)  # small delay to be polite to the server

print("\nAll downloads completed.")
