import os
import sys
import urllib.request

url = "https://github.com/NatLabRockies/EnergyPlus/releases/download/v24.2.0/EnergyPlus-24.2.0-e7ecb2d53b-Windows-x86_64.exe"
dest = "EnergyPlus-24.2.0-e7ecb2d53b-Windows-x86_64.exe"

print(f"Downloading EnergyPlus 24.2.0 installer from: {url}")

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp, open(dest, "wb") as f:
    total_size = int(resp.headers.get('content-length', 0))
    downloaded = 0
    chunk_size = 1024 * 1024 # 1MB

    while True:
        chunk = resp.read(chunk_size)
        if not chunk:
            break
        f.write(chunk)
        downloaded += len(chunk)
        if total_size:
            pct = (downloaded / total_size) * 100
            print(f"Progress: {downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({pct:.1f}%)", end="\r")

print(f"\nDownload complete: {dest} ({os.path.getsize(dest) / (1024*1024):.1f} MB)")
