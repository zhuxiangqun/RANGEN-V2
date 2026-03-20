import json
import time
import sys
import os

def monitor():
    file_path = "data/knowledge_management/import_progress.json"
    print(f"正在监控 {file_path}...")
    print("按 Ctrl+C 退出")
    
    last_processed = -1
    
    while True:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                processed = len(data.get('processed_item_indices', []))
                total = data.get('total_items', 0)
                failed = len(data.get('failed_item_indices', []))
                
                # Always print if it's the first time or if progress changed
                if processed != last_processed:
                    timestamp = time.strftime("%H:%M:%S")
                    percent = (processed / total * 100) if total > 0 else 0
                    bar_len = 30
                    filled = int(bar_len * percent / 100)
                    bar = '█' * filled + '░' * (bar_len - filled)
                    
                    print(f"[{timestamp}] 进度: {percent:5.1f}% |{bar}| ({processed}/{total}) 失败: {failed}")
                    last_processed = processed
            else:
                print("等待进度文件创建...")
                
            time.sleep(2)
        except KeyboardInterrupt:
            break
        except Exception as e:
            # print(f"Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    monitor()
