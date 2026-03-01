#!/usr/bin/env python3
"""
Comparison script: Standard Retrieval vs Small-to-Big Retrieval
Visualizes the difference in context window size.
"""

import sys
import os
import logging
import textwrap

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge_management_system.api.service_interface import KnowledgeManagementService

# Setup logging
logging.basicConfig(level=logging.ERROR) # Only show errors to keep output clean
logger = logging.getLogger(__name__)

def print_separator(char="-", length=80):
    print(char * length)

def compare_modes():
    print_separator("=")
    print("🚀 Small-to-Big Retrieval Comparison Test")
    print_separator("=")
    
    service = KnowledgeManagementService()
    
    # 0. Ensure Data Exists (Import if needed)
    print("Ensuring test data exists...")
    large_content = "This is a sentence in a large document. " * 500
    large_content = "## Section 1\n" + large_content + "\n\n## Section 2\n" + large_content
    metadata = {"source": "test_script_retrieval", "title": "Large Retrieval Doc"}
    service.import_knowledge(
        data=[{"content": large_content, "metadata": metadata}],
        source_type="list",
        modality="text"
    )
    
    query = "sentence in a large document"
    print(f"Query: '{query}'")
    print_separator()
    
    # 1. Standard Retrieval
    print("running Standard Retrieval (expand_context=False)...")
    results_std = service.query_knowledge(
        query=query,
        top_k=1,
        similarity_threshold=0.1, # Ensure we find it
        expand_context=False,
        use_rerank=False
    )
    
    if not results_std:
        print("❌ No results found! Please run scripts/test_small_to_big.py first to populate data.")
        return

    std_result = results_std[0]
    std_content = std_result.get('content', '')
    
    # 2. Small-to-Big Retrieval
    print("running Small-to-Big Retrieval (expand_context=True)...")
    results_exp = service.query_knowledge(
        query=query,
        top_k=1,
        similarity_threshold=0.1, # Ensure we find it
        expand_context=True,
        use_rerank=False
    )
    
    exp_result = results_exp[0]
    # In the current implementation, 'content' is the chunk, 'full_content' is the parent
    exp_content_chunk = exp_result.get('content', '')
    exp_full_content = exp_result.get('full_content', '')
    
    # 3. Visualization
    print("\n📊 Comparison Results:\n")
    
    print(f"{'Metric':<20} | {'Standard Mode':<25} | {'Small-to-Big Mode':<25}")
    print(f"{'-'*20}-+-{'-'*25}-+-{'-'*25}")
    
    print(f"{'Retrieved ID':<20} | {std_result['knowledge_id'][:8]:<25} | {exp_result['knowledge_id'][:8]:<25}")
    print(f"{'Parent ID':<20} | {'N/A':<25} | {str(exp_result.get('metadata', {}).get('parent_id', 'N/A'))[:8]:<25}")
    print(f"{'Context Length':<20} | {len(std_content):<25} | {len(exp_full_content):<25}")
    
    gain = len(exp_full_content) / len(std_content) if len(std_content) > 0 else 0
    print(f"{'Context Gain':<20} | {'1.0x':<25} | {f'{gain:.1f}x':<25}")
    
    print_separator()
    print("📝 Content Preview (Standard - First 200 chars):")
    print(textwrap.fill(std_content[:200] + "...", width=80))
    
    print_separator()
    print("📝 Content Preview (Small-to-Big - First 200 chars):")
    print(textwrap.fill(exp_full_content[:200] + "...", width=80))
    
    print_separator()
    print("📝 Content Preview (Small-to-Big - Last 200 chars):")
    print(textwrap.fill("..." + exp_full_content[-200:], width=80))
    
    print_separator("=")
    if len(exp_full_content) > len(std_content):
        print("✅ SUCCESS: Small-to-Big successfully retrieved the full parent document context.")
    else:
        print("❌ FAILURE: Small-to-Big did not provide more context than standard.")

if __name__ == "__main__":
    compare_modes()
