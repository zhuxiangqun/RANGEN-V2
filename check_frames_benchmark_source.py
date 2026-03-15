
import sys
import os
import json

def check_dataset_content():
    base_path = "data/frames-benchmark"
    if not os.path.exists(base_path):
        print(f"Directory {base_path} does not exist.")
        return

    files = [f for f in os.listdir(base_path) if f.endswith('.json')]
    
    print(f"Found files: {files}")
    
    for fname in files:
        fpath = os.path.join(base_path, fname)
        print(f"\n--- Checking {fname} ---")
        try:
            with open(fpath, 'r') as f:
                data = json.load(f)
                
            # Check first entry
            if isinstance(data, list) and len(data) > 0:
                print(f"Type: List of {len(data)} items")
                entry = data[0]
                print(json.dumps(entry, indent=2)[:1000]) 
            elif isinstance(data, dict):
                print(f"Type: Dict with keys {list(data.keys())}")
                # Maybe explore deeper
        except Exception as e:
            print(f"Error reading {fname}: {e}")

if __name__ == "__main__":
    check_dataset_content()
