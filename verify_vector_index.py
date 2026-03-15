
import sys
import os
import json
import numpy as np
import faiss
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.getcwd())

def verify_index():
    index_path = "data/knowledge_management/vector_index.bin"
    mapping_path = "data/knowledge_management/vector_index.mapping.json"
    metadata_path = "data/knowledge_management/metadata.json"
    
    if not os.path.exists(index_path):
        print(f"Index file not found: {index_path}")
        return
        
    if not os.path.exists(mapping_path):
        print(f"Mapping file not found: {mapping_path}")
        return
        
    try:
        index = faiss.read_index(index_path)
        print(f"Index loaded successfully.")
        print(f"Total vectors in index: {index.ntotal}")
        print(f"Index dimension: {index.d}")
        
        # Check Metadata for item_index coverage
        if os.path.exists(metadata_path):
            print(f"\nAnalyzing Metadata...")
            with open(metadata_path, 'r') as f:
                metadata_content = json.load(f)
                entries = metadata_content.get('entries', {})
                print(f"Total metadata entries: {len(entries)}")
                
                processed_item_indices = set()
                for key, entry in entries.items():
                    meta = entry.get('metadata', {})
                    if 'item_index' in meta:
                        processed_item_indices.add(meta['item_index'])
                
                print(f"Unique FRAMES items processed: {len(processed_item_indices)}")
                if processed_item_indices:
                    print(f"Min item index: {min(processed_item_indices)}")
                    print(f"Max item index: {max(processed_item_indices)}")
                    
                    # Check for gaps
                    all_indices = set(range(min(processed_item_indices), max(processed_item_indices) + 1))
                    missing = all_indices - processed_item_indices
                    if missing:
                        print(f"Missing indices count: {len(missing)}")
                        if len(missing) < 20:
                            print(f"Missing indices: {sorted(list(missing))}")
                    else:
                        print("No gaps in processed indices range.")
        
        # Simple retrieval test
        # Generate a random vector of correct dimension
        query_vector = np.random.rand(1, index.d).astype('float32')
        faiss.normalize_L2(query_vector)
        
        k = 5
        distances, indices = index.search(query_vector, k)
        
        print(f"\nRetrieval Test (Random Vector):")
        for i in range(k):
            idx = indices[0][i]
            dist = distances[0][i]
            if idx != -1:
                print(f"Rank {i+1}: Index {idx}, Distance {dist}")
            else:
                print(f"Rank {i+1}: Not found")
                
    except Exception as e:
        print(f"Error verifying index: {e}")

if __name__ == "__main__":
    verify_index()
