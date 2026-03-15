
import json
import sys
import os
import re
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.getcwd())

from knowledge_management_system.utils.wikipedia_fetcher import WikipediaFetcher
from knowledge_management_system.utils.logger import get_logger

logger = get_logger()

def extract_wikipedia_links_from_item(item: Dict[str, Any]) -> List[str]:
    """从单个FRAMES数据项中提取Wikipedia链接"""
    wikipedia_links = []
    
    def parse_wikipedia_links(value):
        """解析Wikipedia链接的辅助函数"""
        parsed_links = []
        
        if isinstance(value, list):
            parsed_links = [link for link in value if isinstance(link, str) and 'wikipedia.org' in link.lower() and link.strip()]
        elif isinstance(value, str):
            # 方式1: JSON解析
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    parsed_links = [link for link in parsed if isinstance(link, str) and 'wikipedia.org' in link.lower() and link.strip()]
            except:
                pass
            
            # 方式2: ast.literal_eval
            if not parsed_links:
                try:
                    import ast
                    parsed = ast.literal_eval(value)
                    if isinstance(parsed, list):
                        parsed_links = [link for link in parsed if isinstance(link, str) and 'wikipedia.org' in link.lower() and link.strip()]
                except:
                    pass
            
            # 方式3: 正则表达式
            if not parsed_links:
                import re
                url_pattern = r'https?://[^\s,\[\]]*wikipedia\.org[^\s,\[\]]*'
                found_urls = re.findall(url_pattern, value)
                parsed_links = [url.strip("'\"") for url in found_urls if url.strip()]
        
        return parsed_links
    
    # 优先从 wiki_links 字段提取
    if 'wiki_links' in item and item['wiki_links']:
        links = parse_wikipedia_links(item['wiki_links'])
        wikipedia_links.extend(links)
    
    # 如果 wiki_links 没有或为空，尝试从 evidence 字段提取
    if not wikipedia_links and 'evidence' in item and item['evidence']:
        links = parse_wikipedia_links(item['evidence'])
        wikipedia_links.extend(links)
    
    # 去重
    return list(set([link for link in wikipedia_links if link and link.strip()]))

def diagnose_item(item_index):
    dataset_path = "data/knowledge_management/frames_dataset_complete.json"
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        frames_data = json.load(f)
        
    if item_index >= len(frames_data):
        print(f"Item index {item_index} out of range")
        return

    item = frames_data[item_index]
    print(f"🔍 Diagnosing Item {item_index}")
    
    # Use the extraction logic from the main script
    wiki_links = extract_wikipedia_links_from_item(item)
    
    if not wiki_links:
        print("❌ No wiki_links found in item (using extraction logic)")
        return
        
    print(f"Found {len(wiki_links)} wiki links: {wiki_links}")
    
    fetcher = WikipediaFetcher()
    
    for link in wiki_links:
        print(f"\nTrying to fetch: {link}")
        try:
            print(f"URL: {link}")
            
            # Using fetch_page_content instead of fetch_page
            content = fetcher.fetch_page_content(link)
            if content:
                print(f"✅ Successfully fetched content (title: {content.get('title')})")
            else:
                print(f"❌ Failed to fetch content for {link} (Result is None)")
                
        except Exception as e:
            print(f"❌ Exception while fetching {link}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    diagnose_item(146)
