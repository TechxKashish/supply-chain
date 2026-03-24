import json
import os

dataset_path = r"C:\Users\radhi\Downloads\dodge\dataset"

for folder in sorted(os.listdir(dataset_path)):
    folder_path = os.path.join(dataset_path, folder)
    
    if not os.path.isdir(folder_path):
        continue
    
    jsonl_file = None
    for f in os.listdir(folder_path):
        if f.endswith(".jsonl"):
            jsonl_file = os.path.join(folder_path, f)
            break
    
    if not jsonl_file:
        print(f"--- {folder} --- NO JSONL FILE FOUND")
        continue

    records = []
    with open(jsonl_file, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 2:
                break
            line = line.strip()
            if line:
                records.append(json.loads(line))

    print(f"\n{'='*60}")
    print(f"TABLE: {folder}")
    print(f"COLUMNS: {list(records[0].keys()) if records else 'EMPTY'}")
    print(f"SAMPLE: {json.dumps(records[0], indent=2) if records else 'N/A'}")