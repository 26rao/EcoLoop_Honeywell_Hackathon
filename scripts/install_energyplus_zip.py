import os
import sys
import zipfile
import urllib.request

url = "https://github.com/NatLabRockies/EnergyPlus/releases/download/v24.2.0/EnergyPlus-24.2.0-e7ecb2d53b-Windows-x86_64.zip"
zip_dest = "EnergyPlus-24.2.0-e7ecb2d53b-Windows-x86_64.zip"
target_dir = r"C:\EnergyPlusV24-2-0"

if not os.path.exists(zip_dest):
    print(f"Downloading EnergyPlus 24.2.0 ZIP archive from: {url}")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp, open(zip_dest, "wb") as f:
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    print("Download completed.")

print(f"Extracting {zip_dest} to {target_dir}...")
os.makedirs(target_dir, exist_ok=True)

with zipfile.ZipFile(zip_dest, 'r') as zip_ref:
    # Unpack contents cleanly
    for file_info in zip_ref.infolist():
        # Strip top-level directory prefix if present
        parts = file_info.filename.split('/', 1)
        if len(parts) > 1 and parts[1]:
            extracted_path = os.path.join(target_dir, parts[1])
            if file_info.is_dir():
                os.makedirs(extracted_path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(extracted_path), exist_ok=True)
                with zip_ref.open(file_info) as src, open(extracted_path, 'wb') as dst:
                    dst.write(src.read())

print(f"Successfully installed EnergyPlus to {target_dir}!")
