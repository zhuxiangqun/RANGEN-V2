import json
import time
import os
import sys

def monitor():
    file_path = "data/knowledge_management/vector_import_progress.json"
    print(f"正在监控 {file_path}...")
    print("按 Ctrl+C 退出")
    
    last_processed = -1
    
    while True:
        try:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    processed = len(data.get('processed_item_indices', []))
                    total = data.get('total_items', 824)
                    failed = len(data.get('failed_item_indices', []))
                    last_update = data.get('last_update', 'Unknown')
                    
                    # Calculate percentage
                    percent = (processed / total * 100) if total > 0 else 0
                    bar_len = 30
                    filled = int(bar_len * percent / 100)
                    bar = '█' * filled + '░' * (bar_len - filled)
                    
                    # Clear line and print
                    sys.stdout.write(f"\r[{last_update.split('T')[-1][:8]}] 进度: {percent:5.1f}% |{bar}| ({processed}/{total}) 失败: {failed}")
                    sys.stdout.flush()
                    
                except json.JSONDecodeError:
                    pass # File might be being written to
            else:
                sys.stdout.write("\r等待进度文件创建...")
                sys.stdout.flush()
                
            time.sleep(2)
        except KeyboardInterrupt:
            print("\n监控已停止")
            break
        except Exception as e:
            # print(f"\nError: {e}")
            time.sleep(2)

if __name__ == "__main__":
    monitor()
