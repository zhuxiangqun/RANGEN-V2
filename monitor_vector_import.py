import json
import time
import sys
import os
from datetime import datetime

PROGRESS_FILES = [
    "data/knowledge_management/vector_import_progress.json",
    "data/knowledge_management/import_progress.json"
]

def load_progress():
    try:
        latest = None
        latest_data = None
        for path in PROGRESS_FILES:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                last_update = data.get('last_update')
                if last_update:
                    try:
                        ts = datetime.fromisoformat(last_update)
                    except Exception:
                        ts = datetime.fromtimestamp(os.path.getmtime(path))
                else:
                    ts = datetime.fromtimestamp(os.path.getmtime(path))
                if latest is None or ts > latest:
                    latest = ts
                    latest_data = (path, data)
        return latest_data
    except Exception:
        return None

def monitor():
    print("🚀 Starting Vector Knowledge Base Build Monitor...")
    
    last_processed_count = 0
    start_time = time.time()
    
    while True:
        result = load_progress()
        if result:
            progress_file, progress = result
            processed_indices = set(progress.get('processed_item_indices', []))
            failed_indices = set(progress.get('failed_item_indices', []))
            total_items = progress.get('total_items', 824)
            
            processed_count = len(processed_indices)
            failed_count = len(failed_indices)
            current_count = processed_count + failed_count
            
            percentage = (current_count / total_items) * 100 if total_items > 0 else 0
            bar_length = 40
            filled_length = int(bar_length * current_count // total_items) if total_items > 0 else 0
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            
            elapsed = time.time() - start_time
            items_since_start = processed_count - last_processed_count
            speed = items_since_start / elapsed if elapsed > 0 else 0
            
            status_line = (f"\rProgress: |{bar}| {percentage:.1f}% "
                           f"[{current_count}/{total_items}] "
                           f"(Success: {processed_count}, Failed: {failed_count}) "
                           f"[file: {os.path.basename(progress_file)}]")
            
            sys.stdout.write("\033[K")
            sys.stdout.write(status_line)
            sys.stdout.flush()
            
        time.sleep(1)

if __name__ == "__main__":
    try:
        monitor()
    except KeyboardInterrupt:
        print("\n\nMonitor stopped.")
