"""Download preview images from collected posts."""
import json
import os
import requests

os.makedirs("data/preview", exist_ok=True)

# Find the collected JSON file
raw_dir = "data/raw"
files = [f for f in os.listdir(raw_dir) if f.endswith(".json")]
if not files:
    print("No raw JSON files found")
    exit(1)

filepath = os.path.join(raw_dir, files[0])
print(f"Reading {filepath}")

with open(filepath) as f:
    posts = json.load(f)

for i, post in enumerate(posts):
    for j, url in enumerate(post["imageUrls"][:2]):
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                path = f"data/preview/post{i+1}_img{j+1}.jpg"
                with open(path, "wb") as out:
                    out.write(resp.content)
                print(f"Saved {path} ({len(resp.content)//1024}KB)")
            else:
                print(f"Failed post{i+1}_img{j+1}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"Failed post{i+1}_img{j+1}: {e}")
