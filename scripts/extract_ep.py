import os
import shutil
import zipfile

src_zip = r"c:\Users\HP\OneDrive\Attachments\Desktop\Honeywell Hackathon\EnergyPlus-24.2.0-e7ecb2d53b-Windows-x86_64.zip"
target_dir = r"C:\EnergyPlusV24-2-0"

os.makedirs(target_dir, exist_ok=True)
print(f"Extracting {src_zip} to {target_dir}...")

with zipfile.ZipFile(src_zip, 'r') as z:
    z.extractall(target_dir)

print("Extraction completed!")
