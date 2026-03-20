
import json
import os
from pathlib import Path

def reconstruct_progress():
    metadata_path = "data/knowledge_management/metadata.json"
    progress_path = "data/knowledge_management/vector_import_progress.json"
    
    if not os.path.exists(metadata_path):
        print(f"Metadata file not found: {metadata_path}")
        return
        
    print(f"Reading metadata from {metadata_path}...")
    with open(metadata_path, 'r') as f:
        metadata_content = json.load(f)
        
    entries = metadata_content.get('entries', {})
    processed_indices = set()
    
    for key, entry in entries.items():
        meta = entry.get('metadata', {})
        if 'item_index' in meta:
            processed_indices.add(meta['item_index'])
            
    print(f"Found {len(processed_indices)} unique processed item indices.")
    
    progress_data = {
        'processed_item_indices': sorted(list(processed_indices)),
        'failed_item_indices': [],
        'total_items': 824,  # Assuming FRAMES dataset size
        'start_time': None,
        'last_update': None
    }
    
    # Write to progress file
    os.makedirs(os.path.dirname(progress_path), exist_ok=True)
    with open(progress_path, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully reconstructed progress file at {progress_path}")

if __name__ == "__main__":
    reconstruct_progress()
