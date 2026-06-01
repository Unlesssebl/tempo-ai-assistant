import os
import yaml
import glob
from pathlib import Path

data_dir = Path("data")
broken_files = []

for filepath in data_dir.rglob("*.md"):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    if content.startswith("---"):
        end_idx = content.find("---", 3)
        if end_idx != -1:
            yaml_content = content[3:end_idx]
            try:
                yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                broken_files.append((str(filepath), str(e)))

print(f"Total markdown files checked: {len(list(data_dir.rglob('*.md')))}")
if not broken_files:
    print("ALL FILES OK!")
else:
    print(f"FOUND {len(broken_files)} BROKEN FILES:")
    for f, err in broken_files:
        print(f"\n--- {f} ---")
        print(err)
