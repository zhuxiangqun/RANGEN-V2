#!/usr/bin/env python3
"""
RANGEN前端监控系统后端API
独立运行，不与其他系统耦合
"""

import os
import re
import json
import subprocess
import signal
import time
import threading
import requests
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
# 🚀 修复：配置CORS，允许所有来源和所有方法
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "expose_headers": ["Content-Type", "Cache-Control", "X-Accel-Buffering"],
        "supports_credentials": False
    }
})

# 🚀 新增：添加全局after_request处理器，确保所有响应都有CORS头
@app.after_request
def after_request(response):
    """为所有响应添加CORS头"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
    response.headers.add('Access-Control-Expose-Headers', 'Content-Type, Cache-Control, X-Accel-Buffering')
    response.headers.add('Access-Control-Max-Age', '3600')
    return response

# 项目根目录（相对于backend目录）
ROOT_DIR = Path(__file__).parent.parent.parent
LOG_FILE = ROOT_DIR / "research_system.log"
EVALUATION_SCRIPT = ROOT_DIR / "scripts" / "run_evaluation.sh"
EVALUATION_REPORT = ROOT_DIR / "comprehensive_eval_results" / "evaluation_report.md"
TENSORBOARD_LOG_DIR = ROOT_DIR / "tensorboard_logs"
TENSORBOARD_LOG_DIR.mkdir(exist_ok=True)

# RANGEN主API地址（用于MCP管理）
RANGEN_API_BASE = "http://localhost:8000"

# TensorBoard 进程管理
tensorboard_process = None
tensorboard_port = 6006

# 🚀 改进：任务状态管理（用于异步执行）
running_tasks = {}  # {task_id: {type, status, process, start_time, output}}
task_counter = 0

# 🚀 修复：日志解析缓存，避免重复读取整个文件
_log_parse_cache = {
    "last_modified": 0,
    "last_size": 0,
    "last_position": 0,
    "cached_data": None,
    "cache_time": 0
}
CACHE_TTL = 2.0  # 缓存有效期2秒


def parse_log_file():
    """解析日志文件，提取推理过程和智能体调用信息"""
    if not LOG_FILE.exists():
        return {
            "samples": [],
            "agent_calls": []
        }
    
    samples = {}
    agent_calls = []
    current_sample = None
    line_number = 0
    # 🚀 改进：存储最近几行的内容，用于跨行提取耗时信息
    recent_lines = []
    # 🚀 改进：保存当前行的duration_ms，用于跨方法传递
    current_duration_ms = None
    # 🚀 修复：保存待更新耗时的调用记录（用于答案生成和验证）
    pending_duration_updates = {}  # {(sample_id, agent_name): call_index}
    
    try:
        # 🚀 改进：存储最近几行的内容，用于跨行提取耗时信息
        recent_lines = []
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line_number += 1
                line = line.strip()
                # 🚀 改进：保存最近3行，用于跨行提取耗时信息
                recent_lines.append(line)
                if len(recent_lines) > 3:
                    recent_lines.pop(0)
                if not line:
                    continue
                
                # 解析样本开始 - 支持多种格式
                sample_match = re.search(r'FRAMES sample=(\d+)/(\d+).*started', line)
                if sample_match:
                    sample_id = int(sample_match.group(1))
                    current_sample = sample_id
                    # 提取查询文本
                    query_match = re.search(r'query=(.+)', line)
                    query_text = query_match.group(1) if query_match else ""
                    
                    if sample_id not in samples:
                        samples[sample_id] = {
                            "id": sample_id,
                            "query": query_text[:200] if query_text else "",
                            "status": "running",
                            "start_time": None,
                            "end_time": None,
                            "steps": [],
                            "answer": None,
                            "expected_answer": None,
                            "error": None,
                            "confidence": None,
                            "duration": None,
                            "completed": False,
                            "is_running": True,
                            "reasoning_steps_count": 0
                        }
                
                # 解析查询接收（优先使用，包含样本ID）- 🚀 修复：更好地处理查询文本
                query_match = re.search(r'查询接收[：:]\s*(.+)', line)
                if query_match:
                    query_text = query_match.group(1)
                    # 提取样本ID
                    sample_id_match = re.search(r'样本ID=(\d+)', query_text)
                    if sample_id_match:
                        sample_id = int(sample_id_match.group(1))
                        current_sample = sample_id
                        # 清理查询文本（移除样本ID标记和RANGEN查询处理流程开始等）
                        clean_query = re.sub(r'样本ID=\d+[，,]?\s*', '', query_text).strip()
                        clean_query = re.sub(r'RANGEN查询处理流程开始[，,]?\s*', '', clean_query).strip()
                        
                        # 🚀 修复：如果查询文本是字典格式，尝试提取Prompt字段
                        if clean_query.startswith('{') or clean_query.startswith("'"):
                            # 尝试提取Prompt字段
                            prompt_match = re.search(r"'Prompt'[：:]\s*['\"]([^'\"]+)['\"]", clean_query)
                            if prompt_match:
                                clean_query = prompt_match.group(1)
                            else:
                                # 如果无法提取，使用原始文本的前200字符
                                clean_query = clean_query[:200]
                        
                        if sample_id not in samples:
                            samples[sample_id] = {
                                "id": sample_id,
                                "query": clean_query[:200],
                                "status": "running",
                                "start_time": None,
                                "end_time": None,
                                "steps": [],
                                "answer": None,
                                "expected_answer": None,
                                "error": None,
                                "confidence": None,
                                "duration": None,
                                "completed": False,
                                "is_running": True,
                                "reasoning_steps_count": 0
                            }
                        else:
                            if not samples[sample_id]["query"] or samples[sample_id]["query"] == "":
                                samples[sample_id]["query"] = clean_query[:200]
                    elif current_sample and current_sample in samples:
                        # 如果没有样本ID，但当前有样本，更新查询
                        if not samples[current_sample]["query"] or samples[current_sample]["query"] == "":
                            # 同样处理查询文本
                            clean_query = query_text
                            clean_query = re.sub(r'RANGEN查询处理流程开始[，,]?\s*', '', clean_query).strip()
                            if clean_query.startswith('{') or clean_query.startswith("'"):
                                prompt_match = re.search(r"'Prompt'[：:]\s*['\"]([^'\"]+)['\"]", clean_query)
                                if prompt_match:
                                    clean_query = prompt_match.group(1)
                            samples[current_sample]["query"] = clean_query[:200]
                
                # 解析期望答案
                expected_answer_match = re.search(r'期望答案[：:]\s*(.+)', line)
                if expected_answer_match and current_sample:
                    if current_sample in samples:
                        samples[current_sample]["expected_answer"] = expected_answer_match.group(1)[:200]
                
                # 解析推理开始时间
                start_time_match = re.search(r'(?:样本)?推理开始时间[：:]\s*([\d.]+)', line)
                if start_time_match:
                    start_time = float(start_time_match.group(1))
                    if current_sample and current_sample in samples:
                        samples[current_sample]["start_time"] = start_time
                
                # 解析推理结束时间
                end_time_match = re.search(r'(?:样本)?推理结束时间[：:]\s*([\d.]+)', line)
                if end_time_match:
                    end_time = float(end_time_match.group(1))
                    if current_sample and current_sample in samples:
                        samples[current_sample]["end_time"] = end_time
                        if samples[current_sample]["start_time"]:
                            samples[current_sample]["duration"] = end_time - samples[current_sample]["start_time"]
                
                # 解析推理步骤（增强版，支持多种格式）
                step_match = re.search(r'🧠 推理步骤 (\d+)[：:]\s*(\w+)\s*-\s*(.+)', line)
                if step_match:
                    step_num = int(step_match.group(1))
                    step_type = step_match.group(2)
                    step_desc = step_match.group(3)
                    if current_sample and current_sample in samples:
                        samples[current_sample]["steps"].append({
                            "number": step_num,
                            "type": step_type,
                            "description": step_desc,
                            "timestamp": time.time()
                        })
                        samples[current_sample]["reasoning_steps_count"] = max(
                            samples[current_sample]["reasoning_steps_count"],
                            step_num
                        )
                
                # 🚀 修复：也解析"查询完成"信息，更新样本状态
                complete_match = re.search(r'查询完成[：:]\s*success=(True|False)', line)
                if complete_match:
                    success = complete_match.group(1) == "True"
                    # 尝试提取样本ID
                    sample_id_match = re.search(r'样本ID=(\d+)', line)
                    if sample_id_match:
                        sample_id = int(sample_id_match.group(1))
                        current_sample = sample_id
                        if sample_id in samples:
                            samples[sample_id]["status"] = "completed" if success else "error"
                            samples[sample_id]["completed"] = success
                            samples[sample_id]["is_running"] = False
                    elif current_sample and current_sample in samples:
                        samples[current_sample]["status"] = "completed" if success else "error"
                        samples[current_sample]["completed"] = success
                        samples[current_sample]["is_running"] = False
                
                # 解析推理步骤数
                steps_count_match = re.search(r'推理步骤数[：:]\s*(\d+)', line)
                if steps_count_match and current_sample:
                    if current_sample in samples:
                        samples[current_sample]["reasoning_steps_count"] = int(steps_count_match.group(1))
                
                # 解析FRAMES sample完成信息（增强版，提取answer）
                frames_complete_match = re.search(r'FRAMES sample=(\d+)/(\d+).*success=(True|False).*took=([\d.]+)s', line)
                if frames_complete_match:
                    sample_id = int(frames_complete_match.group(1))
                    success = frames_complete_match.group(3) == "True"
                    duration = float(frames_complete_match.group(4))
                    if sample_id in samples:
                        samples[sample_id]["status"] = "completed" if success else "error"
                        samples[sample_id]["completed"] = success
                        samples[sample_id]["is_running"] = False
                        if not samples[sample_id]["duration"]:
                            samples[sample_id]["duration"] = duration
                        
                        # 🚀 修复：从FRAMES完成信息中提取answer
                        answer_match = re.search(r'answer=([^\s]+)', line)
                        if answer_match:
                            answer_text = answer_match.group(1).strip()
                            if answer_text and answer_text != 'None':
                                samples[sample_id]["answer"] = answer_text[:500]
                
                # 解析系统答案（多种格式）
                answer_match = re.search(r'(?:系统答案|最终答案|答案)[：:]\s*(.+)', line)
                if answer_match and current_sample:
                    if current_sample in samples:
                        answer_text = answer_match.group(1).strip()
                        # 跳过无效答案标记
                        if answer_text and not answer_text.startswith('[') and '无法提取' not in answer_text:
                            samples[current_sample]["answer"] = answer_text[:500]
                
                # 解析置信度
                confidence_match = re.search(r'(?:结果)?置信度[：:]\s*([\d.]+)', line)
                if confidence_match and current_sample:
                    if current_sample in samples:
                        samples[current_sample]["confidence"] = float(confidence_match.group(1))
                
                # 解析错误信息
                if "error" in line.lower() or "失败" in line or "异常" in line:
                    if current_sample and current_sample in samples:
                        if not samples[current_sample]["error"]:
                            samples[current_sample]["error"] = line[:200]
                            samples[current_sample]["status"] = "error"
                            samples[current_sample]["is_running"] = False
                
                # 🚀 改进：解析智能体调用（从多种日志格式中提取）
                # 提取耗时信息（支持多种格式，包括前后文）
                # 使用局部变量，避免影响全局
                duration_ms = current_duration_ms if current_duration_ms is not None else None
                current_duration_ms = None  # 重置全局变量
                
                duration_patterns = [
                    # 🚀 修复：优先匹配具体的耗时模式（答案生成和验证）
                    r'推导最终答案耗时[：:]\s*([\d.]+)\s*秒',  # ⏱️ 推导最终答案耗时: 1.23秒
                    r'答案合理性验证耗时[：:]\s*([\d.]+)\s*秒',  # ⏱️ 答案合理性验证耗时: 1.23秒
                    r'答案提取[：:]\s*([\d.]+)\s*秒',  # ⏱️ 答案提取: 1.23秒
                    r'验证耗时[：:]\s*([\d.]+)\s*秒',  # 验证耗时: 1.23秒
                    r'验证时间[：:]\s*([\d.]+)\s*秒',  # 验证时间: 1.23秒
                    # 通用耗时模式
                    r'took=([\d.]+)s',  # took=1.23s
                    r'耗时[：:]\s*([\d.]+)\s*秒',  # 耗时: 1.23秒
                    r'耗时[：:]\s*([\d.]+)\s*ms',  # 耗时: 123ms
                    r'duration[：:]\s*([\d.]+)',  # duration: 1.23
                    r'用时[：:]\s*([\d.]+)\s*秒',  # 用时: 1.23秒
                    r'执行时间[：:]\s*([\d.]+)\s*秒',  # 执行时间: 1.23秒
                    r'执行耗时[：:]\s*([\d.]+)\s*秒',  # 执行耗时: 1.23秒
                    r'(\d+\.?\d*)\s*秒',  # 通用：1.23秒（作为最后备选）
                    r'(\d+\.?\d*)\s*ms',  # 通用：123ms（作为最后备选）
                ]
                for pattern in duration_patterns:
                    dur_match = re.search(pattern, line, re.IGNORECASE)
                    if dur_match:
                        dur_value = float(dur_match.group(1))
                        # 如果是秒，转换为毫秒
                        if 'ms' not in pattern.lower():
                            duration_ms = int(dur_value * 1000)
                        else:
                            duration_ms = int(dur_value)
                        # 只使用第一个匹配的耗时信息
                        break
                
                # 🚀 改进：如果当前行没有耗时信息，尝试从后续几行中查找
                # 这可以处理耗时信息在下一行的情况
                if duration_ms is None and step_match:
                    # 对于推理步骤，尝试从步骤描述中提取耗时
                    if step_desc:
                        for pattern in duration_patterns:
                            dur_match = re.search(pattern, step_desc, re.IGNORECASE)
                            if dur_match:
                                dur_value = float(dur_match.group(1))
                                if 'ms' not in pattern.lower():
                                    duration_ms = int(dur_value * 1000)
                                else:
                                    duration_ms = int(dur_value)
                                break
                
                # 方法1: 从推理步骤中提取
                if step_match and current_sample:
                    step_type = step_match.group(2)
                    # 根据步骤类型推断智能体调用
                    # 🚀 修复：支持更多步骤类型名称
                    agent_mapping = {
                        'evidence': ('knowledge_agent', '知识检索', '检索相关证据和知识'),
                        'reasoning': ('reasoning_agent', '推理分析', '进行逻辑推理和推导'),
                        'answer': ('answer_agent', '答案生成', '生成最终答案'),
                        'validation': ('validation_agent', '结果验证', '验证答案的正确性'),
                        # 新增：支持系统实际使用的步骤类型
                        'evidence_gathering': ('knowledge_agent', '知识检索', '检索相关证据和知识'),
                        'query_analysis': ('reasoning_agent', '查询分析', '分析查询内容和意图'),
                        'logical_deduction': ('reasoning_agent', '逻辑推理', '进行逻辑推理和推导'),
                        'answer_synthesis': ('answer_agent', '答案综合', '综合生成最终答案'),
                        'pattern_recognition': ('reasoning_agent', '模式识别', '识别和分析模式'),
                        'causal_reasoning': ('reasoning_agent', '因果推理', '进行因果推理'),
                        'analogical_reasoning': ('reasoning_agent', '类比推理', '进行类比推理'),
                        'mathematical_reasoning': ('reasoning_agent', '数学推理', '进行数学推理'),
                        'verification': ('validation_agent', '结果验证', '验证答案的正确性'),
                        'fact_checking': ('validation_agent', '事实核查', '核查事实准确性')
                    }
                    if step_type in agent_mapping:
                        agent_name, agent_role, agent_purpose = agent_mapping[step_type]
                        sample_id_for_call = current_sample
                        # 提取步骤结论作为结果
                        step_result = ""
                        if step_desc:
                            # 尝试从步骤描述中提取结论
                            conclusion_match = re.search(r'结论[：:]\s*(.+?)(?:\n|$)', step_desc)
                            if conclusion_match:
                                step_result = conclusion_match.group(1).strip()[:200]
                            else:
                                # 如果没有明确的结论，使用步骤描述的后半部分
                                step_result = step_desc[-200:] if len(step_desc) > 200 else step_desc
                        
                        # 检查是否已存在相同的调用（避免重复）
                        call_key = (current_sample, agent_name)
                        existing_call = next((c for c in agent_calls if (c.get('sample_id'), c.get('to')) == call_key), None)
                        if existing_call:
                            # 更新现有调用的信息
                            if duration_ms is not None:
                                existing_call["duration"] = duration_ms
                            if step_result:
                                existing_call["result"] = step_result
                            if not existing_call.get("purpose"):
                                existing_call["purpose"] = agent_purpose
                            if not existing_call.get("role"):
                                existing_call["role"] = agent_role
                        else:
                            agent_calls.append({
                                "from": "system",
                                "to": agent_name,
                                "role": agent_role,
                                "purpose": agent_purpose,
                                "timestamp": time.time(),
                                "duration": duration_ms if duration_ms is not None else None,
                                "success": True,
                                "query": step_desc[:150] if step_desc else "",
                                "result": step_result,
                                "sample_id": sample_id_for_call
                            })
                        # 🚀 修复：保存duration_ms到全局变量，供方法2使用
                        if duration_ms is not None:
                            current_duration_ms = duration_ms
                        duration_ms = None  # 重置局部变量，避免影响方法2的重新提取
                
                # 方法2: 从日志关键词中提取
                # 🚀 改进：重新提取耗时信息（因为可能被方法1重置了）
                if duration_ms is None:
                    # 先尝试使用之前保存的duration_ms
                    if current_duration_ms is not None:
                        duration_ms = current_duration_ms
                        current_duration_ms = None  # 使用后重置
                    else:
                        # 重新从当前行提取
                        for pattern in duration_patterns:
                            dur_match = re.search(pattern, line, re.IGNORECASE)
                            if dur_match:
                                dur_value = float(dur_match.group(1))
                                if 'ms' not in pattern.lower():
                                    duration_ms = int(dur_value * 1000)
                                else:
                                    duration_ms = int(dur_value)
                                break
                agent_patterns = [
                    (r'(知识检索|knowledge.*retrieval|检索知识)', 'knowledge_agent', '知识检索', '检索相关证据和知识'),
                    (r'(推理|reasoning|推导|分析)', 'reasoning_agent', '推理分析', '进行逻辑推理和推导'),
                    # 🚀 修复：改进答案生成和验证的匹配模式，确保能匹配到相关日志
                    (r'(推导最终答案|答案生成|生成答案|answer.*generation|调用LLM推导答案|答案综合|answer.*synthesis|最终答案|答案提取)', 'answer_agent', '答案生成', '生成最终答案'),
                    (r'(答案合理性验证|验证|validation|校验|结果验证|答案验证|验证答案|验证耗时)', 'validation_agent', '结果验证', '验证答案的正确性'),
                    (r'(引用|citation|参考文献)', 'citation_agent', '引用生成', '生成答案引用'),
                    (r'(分析|analysis)', 'analysis_agent', '数据分析', '分析查询和数据'),
                    (r'(事实验证|fact.*verification)', 'verification_agent', '事实验证', '验证事实准确性'),
                    (r'(策略|strategy)', 'strategy_agent', '策略制定', '制定处理策略'),
                    (r'(协调|coordinator)', 'coordinator_agent', '协调管理', '协调多个智能体')
                ]
                
                for pattern, agent_name, agent_role, agent_purpose in agent_patterns:
                    agent_match = re.search(pattern, line, re.IGNORECASE)
                    if agent_match:
                        # 尝试提取调用方
                        from_agent = "system"
                        # 尝试提取样本ID作为上下文
                        sample_id_for_call = current_sample if current_sample else None
                        
                        # 🚀 修复：如果当前行没有耗时信息，尝试从后续几行中查找
                        # 这对于答案生成和验证特别重要，因为它们的耗时可能在后续行中
                        if duration_ms is None:
                            # 检查后续几行（最多5行）
                            future_lines = []
                            try:
                                # 读取后续几行（需要重新打开文件或使用其他方法）
                                # 这里我们使用一个简单的方法：在recent_lines中查找
                                # 但实际上我们需要向前查找，所以暂时跳过
                                pass
                            except:
                                pass
                        
                        # 尝试提取结果信息
                        result_text = ""
                        # 查找结果相关的关键词
                        result_patterns = [
                            r'结果[：:]\s*(.+?)(?:\n|$)',
                            r'result[：:]\s*(.+?)(?:\n|$)',
                            r'答案[：:]\s*(.+?)(?:\n|$)',
                            r'answer[：:]\s*(.+?)(?:\n|$)',
                        ]
                        for rp in result_patterns:
                            r_match = re.search(rp, line, re.IGNORECASE)
                            if r_match:
                                result_text = r_match.group(1).strip()[:200]
                                break
                        
                        # 检查是否已存在相同的调用（避免重复）
                        call_key = (sample_id_for_call, agent_name)
                        existing_call = next((c for c in agent_calls if (c.get('sample_id'), c.get('to')) == call_key), None)
                        if existing_call:
                            # 更新现有调用的信息
                            if duration_ms is not None and not existing_call.get("duration"):
                                existing_call["duration"] = duration_ms
                            if result_text and not existing_call.get("result"):
                                existing_call["result"] = result_text
                            if not existing_call.get("purpose"):
                                existing_call["purpose"] = agent_purpose
                            if not existing_call.get("role"):
                                existing_call["role"] = agent_role
                        else:
                            agent_calls.append({
                                "from": from_agent,
                                "to": agent_name,
                                "role": agent_role,
                                "purpose": agent_purpose,
                                "timestamp": time.time(),
                                "duration": duration_ms if duration_ms is not None else None,
                                "success": "error" not in line.lower() and "失败" not in line and "异常" not in line,
                                "query": line[:150],
                                "result": result_text,
                                "sample_id": sample_id_for_call
                            })
                        # 🚀 修复：对于答案生成和验证，如果还没有耗时信息，标记为待更新
                        if duration_ms is None and (agent_name == 'answer_agent' or agent_name == 'validation_agent'):
                            call_key = (sample_id_for_call, agent_name)
                            if existing_call:
                                # 如果调用已存在，记录其索引以便后续更新
                                call_index = next((i for i, c in enumerate(agent_calls) if (c.get('sample_id'), c.get('to')) == call_key), None)
                                if call_index is not None:
                                    pending_duration_updates[call_key] = call_index
                            else:
                                # 如果调用是新创建的，记录其索引
                                pending_duration_updates[call_key] = len(agent_calls) - 1
                        break
    
    except Exception as e:
        print(f"解析日志文件失败 (行 {line_number}): {e}")
        import traceback
        traceback.print_exc()
    
    # 转换为列表并按ID排序
    samples_list = sorted(samples.values(), key=lambda x: x["id"], reverse=True)
    
    # 🚀 改进：清理智能体调用（去重并排序，按时间戳排序）
    unique_agent_calls = []
    seen_calls = set()
    for call in agent_calls:
        # 使用更精确的去重键：样本ID + 智能体名称
        call_key = (call.get("sample_id"), call["to"])
        if call_key not in seen_calls:
            seen_calls.add(call_key)
            unique_agent_calls.append(call)
    
    # 按时间戳排序
    unique_agent_calls.sort(key=lambda x: x.get("timestamp", 0))
    
    print(f"📊 解析到 {len(unique_agent_calls)} 个智能体调用")
    
    return {
        "samples": samples_list,
        "agent_calls": unique_agent_calls
    }


@app.route('/api/logs', methods=['GET', 'OPTIONS'])
def get_logs():
    """获取日志数据"""
    # 🚀 修复：处理OPTIONS预检请求
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    try:
        data = parse_log_file()
        response = jsonify(data)
        # 🚀 修复：确保响应头包含CORS信息
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        error_response = jsonify({"error": str(e)})
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500


@app.route('/api/logs/stream', methods=['GET', 'OPTIONS'])
def stream_logs():
    """实时流式传输日志更新（SSE）"""
    # 🚀 修复：处理OPTIONS预检请求
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Cache-Control')
        response.headers.add('Access-Control-Expose-Headers', 'Content-Type, Cache-Control, X-Accel-Buffering')
        return response
    
    def event_stream():
        last_modified = 0
        last_size = 0
        if LOG_FILE.exists():
            stat = LOG_FILE.stat()
            last_modified = stat.st_mtime
            last_size = stat.st_size
        
        # 🚀 修复：使用缓存避免频繁解析大文件
        global _log_parse_cache
        
        while True:
            try:
                # 检查文件是否更新
                if LOG_FILE.exists():
                    stat = LOG_FILE.stat()
                    current_modified = stat.st_mtime
                    current_size = stat.st_size
                    
                    # 🚀 修复：减少解析频率，从0.5秒改为2秒
                    # 并且使用缓存机制
                    current_time = time.time()
                    use_cache = (
                        _log_parse_cache["cached_data"] is not None and
                        current_time - _log_parse_cache["cache_time"] < CACHE_TTL and
                        _log_parse_cache["last_modified"] == current_modified and
                        _log_parse_cache["last_size"] == current_size
                    )
                    
                    if current_modified > last_modified or current_size != last_size:
                        last_modified = current_modified
                        last_size = current_size
                        
                        if use_cache:
                            # 使用缓存数据
                            data = _log_parse_cache["cached_data"]
                        else:
                            # 解析日志文件
                            data = parse_log_file()
                            # 更新缓存
                            _log_parse_cache = {
                                "last_modified": current_modified,
                                "last_size": current_size,
                                "last_position": 0,
                                "cached_data": data,
                                "cache_time": current_time
                            }
                        
                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                
                # 🚀 修复：从0.5秒改为2秒，减少CPU和I/O压力
                time.sleep(2.0)
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
                time.sleep(2.0)
    
    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',  # 🚀 修复：允许跨域
            'Access-Control-Allow-Methods': 'GET, OPTIONS',  # 🚀 新增：允许的方法
            'Access-Control-Allow-Headers': 'Content-Type, Cache-Control, X-Requested-With',  # 🚀 新增：允许的请求头
            'Access-Control-Expose-Headers': 'Content-Type, Cache-Control, X-Accel-Buffering'  # 🚀 新增：暴露的响应头
        }
    )


@app.route('/api/core-system/run', methods=['POST', 'OPTIONS'])
def run_core_system():
    """🚀 改进：运行核心系统（异步执行，返回任务ID）"""
    # 🚀 修复：处理OPTIONS预检请求
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    try:
        data = request.get_json() or {}
        sample_count = data.get('sample_count', 10)
        
        # 🚀 新增：清理旧的日志和评测报告，避免产生误解
        try:
            # 清理日志文件
            if LOG_FILE.exists():
                LOG_FILE.unlink()
                print(f"🗑️  已删除旧日志文件: {LOG_FILE}")
            
            # 清理评测报告目录
            eval_results_dir = ROOT_DIR / "comprehensive_eval_results"
            if eval_results_dir.exists():
                # 删除评测报告文件
                eval_report = eval_results_dir / "evaluation_report.md"
                if eval_report.exists():
                    eval_report.unlink()
                    print(f"🗑️  已删除旧评测报告: {eval_report}")
                
                # 删除其他评测结果文件（如JSON文件）
                for result_file in eval_results_dir.glob("*.json"):
                    result_file.unlink()
                    print(f"🗑️  已删除旧评测结果文件: {result_file}")
            
            # 清理evaluation_system目录下的结果文件
            eval_system_dir = ROOT_DIR / "evaluation_system"
            if eval_system_dir.exists():
                for result_file in eval_system_dir.glob("*_results.json"):
                    result_file.unlink()
                    print(f"🗑️  已删除旧评测结果文件: {result_file}")
            
            print("✅ 旧日志和评测报告清理完成")
        except Exception as e:
            print(f"⚠️  清理旧文件时出错（继续执行）: {e}")
        
        core_system_script = ROOT_DIR / "scripts" / "run_core_with_frames.sh"
        if not core_system_script.exists():
            error_response = jsonify({"error": "核心系统脚本不存在"})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 404
        
        # 🚀 改进：生成任务ID
        global task_counter
        task_counter += 1
        task_id = f"core_{task_counter}_{int(time.time())}"
        
        # 🚀 改进：在后台线程中运行，并跟踪状态
        import threading
        
        def run_script():
            try:
                running_tasks[task_id]["status"] = "running"
                running_tasks[task_id]["output"] = f"开始运行核心系统，处理 {sample_count} 个样本...\n"
                
                # 🚀 修复：确保使用项目根目录的.venv环境
                # bash脚本会自动激活.venv，但我们需要确保环境变量正确传递
                env = os.environ.copy()
                # 确保PATH包含项目根目录的.venv（如果存在）
                venv_bin = ROOT_DIR / ".venv" / "bin"
                if venv_bin.exists():
                    current_path = env.get("PATH", "")
                    venv_path = str(venv_bin)
                    if venv_path not in current_path:
                        env["PATH"] = f"{venv_path}:{current_path}"
                
                # 🚀 修复：创建新进程组，以便可以终止所有子进程
                process = subprocess.Popen(
                    ["bash", str(core_system_script), 
                     "--sample-count", str(sample_count),
                     "--data-path", "data/frames_dataset.json"],
                    cwd=str(ROOT_DIR),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env=env,  # 🚀 修复：使用修改后的环境变量
                    preexec_fn=os.setsid  # 🚀 修复：创建新进程组，以便可以终止所有子进程
                )
                
                running_tasks[task_id]["process"] = process
                
                # 🚀 新增：解析进度信息
                current_progress = 0
                total_samples = sample_count
                
                # 实时读取输出
                if process.stdout:
                    for line in iter(process.stdout.readline, ''):
                        if line:
                            running_tasks[task_id]["output"] += line
                            if len(running_tasks[task_id]["output"]) > 10000:  # 限制输出长度
                                running_tasks[task_id]["output"] = running_tasks[task_id]["output"][-5000:]
                            
                            # 🚀 解析进度：查找 "FRAMES sample=X/Y" 或 "样本ID=X" 等模式
                            progress_match = re.search(r'FRAMES sample=(\d+)/(\d+)', line)
                            if progress_match:
                                current_sample = int(progress_match.group(1))  # 当前正在处理的样本编号（从1开始）
                                total_samples = int(progress_match.group(2))
                                running_tasks[task_id]["total_samples"] = total_samples
                            
                            # 🚀 修复：检查日志文件，统计实际已完成的样本数
                            # ⚠️ 严重性能问题修复：不要每行都读取整个日志文件
                            # 改为每10行或每5秒才读取一次
                            if not hasattr(run_script, '_last_log_check'):
                                run_script._last_log_check = 0
                                run_script._last_log_check_time = time.time()
                            
                            should_check_log = False
                            current_time = time.time()
                            # 每10行或每5秒检查一次
                            if (run_script.line_count % 10 == 0) or (current_time - run_script._last_log_check_time > 5):
                                should_check_log = True
                                run_script._last_log_check_time = current_time
                            
                            completed_samples = 0
                            if should_check_log:
                                log_file = ROOT_DIR / "research_system.log"
                                if log_file.exists():
                                    try:
                                        # 🚀 修复：使用更轻量级的方法，只统计完成标记，不读取整个文件
                                        # 使用 tail 命令只读取最后1000行，或者使用文件指针定位
                                        file_size = log_file.stat().st_size
                                        # 如果文件太大（>10MB），只读取最后部分
                                        max_read_size = 10 * 1024 * 1024  # 10MB
                                        read_from_start = 0
                                        if file_size > max_read_size:
                                            read_from_start = file_size - max_read_size
                                        
                                        with open(log_file, 'r', encoding='utf-8') as f:
                                            if read_from_start > 0:
                                                f.seek(read_from_start)
                                                # 跳过可能的不完整行
                                                f.readline()
                                            
                                            # 只读取最后部分内容
                                            log_content = f.read()
                                        
                                        # 🚀 优化：使用更简单的正则表达式，只查找完成标记
                                        # 方法：查找 "FRAMES sample=X/Y" 且包含 "success=True" 或 "查询完成"
                                        completed_sample_ids = set()
                                        # 查找所有包含 success=True 的样本
                                        for match in re.finditer(r'FRAMES sample=(\d+)/(\d+).*?success=True', log_content, re.DOTALL):
                                            completed_sample_ids.add(int(match.group(1)))
                                        # 查找所有包含"查询完成"的样本ID
                                        for match in re.finditer(r'样本ID=(\d+).*?查询完成', log_content, re.DOTALL):
                                            completed_sample_ids.add(int(match.group(1)))
                                        
                                        completed_samples = len(completed_sample_ids)
                                        
                                        # 如果找不到完成标记，使用保守估计
                                        if completed_samples == 0 and current_sample > 0:
                                            completed_samples = max(0, current_sample - 1)
                                    except Exception as e:
                                        print(f"解析日志文件失败: {e}")
                                        # 如果解析失败，使用保守估计
                                        if current_sample > 0:
                                            completed_samples = max(0, current_sample - 1)
                            else:
                                # 不检查日志时，使用上次的值或保守估计
                                if current_sample > 0:
                                    completed_samples = max(0, current_sample - 1)
                            
                            # 🚀 修复：更新进度时，确保不超过总数和当前样本编号
                            # 但不能简单地使用 current_sample，因为可能跳过了某些样本
                            completed_samples = min(completed_samples, total_samples)
                            running_tasks[task_id]["current_progress"] = completed_samples
                            
                            # 🚀 修复：进度百分比计算，如果已完成数等于总数，但任务还在运行，显示99%而不是100%
                            if completed_samples >= total_samples and running_tasks[task_id].get("status") == "running":
                                running_tasks[task_id]["progress_percent"] = 99
                            else:
                                running_tasks[task_id]["progress_percent"] = int((completed_samples / total_samples) * 100) if total_samples > 0 else 0
                            
                            # 🚀 新增：打印进度更新日志，便于调试
                            print(f"📊 进度更新: {completed_samples}/{total_samples} ({running_tasks[task_id]['progress_percent']}%)")
                        
                        # 🚀 新增：即使没有匹配到FRAMES sample，也定期从日志文件更新进度
                        # 每10行输出检查一次日志文件（避免过于频繁）
                        if hasattr(run_script, 'line_count'):
                            run_script.line_count += 1
                        else:
                            run_script.line_count = 0
                        
                        # 每10行或每5秒检查一次日志文件更新进度
                        if run_script.line_count % 10 == 0:
                            log_file = ROOT_DIR / "research_system.log"
                            if log_file.exists() and running_tasks[task_id].get("status") == "running":
                                try:
                                    with open(log_file, 'r', encoding='utf-8') as f:
                                        log_content = f.read()
                                        # 🚀 修复：使用与上面相同的方法统计实际已完成的样本数
                                        completed_sample_ids = set()
                                        # 查找所有包含"查询完成"的样本ID
                                        for match in re.finditer(r'样本ID=(\d+)', log_content):
                                            sample_id = int(match.group(1))
                                            start_pos = max(0, match.start() - 500)
                                            end_pos = min(len(log_content), match.end() + 500)
                                            context = log_content[start_pos:end_pos]
                                            if re.search(r'(?:查询完成|success=(True|False))', context):
                                                completed_sample_ids.add(sample_id)
                                        
                                        # 查找 "FRAMES sample=X/Y" 且包含完成标记的样本
                                        frames_matches = re.findall(r'FRAMES sample=(\d+)/(\d+)', log_content)
                                        for sample_num_str, total_str in frames_matches:
                                            sample_num = int(sample_num_str)
                                            pattern = rf'FRAMES sample={sample_num}/{total_str}.*?(?:查询完成|success=(True|False))'
                                            if re.search(pattern, log_content, re.DOTALL):
                                                completed_sample_ids.add(sample_num)
                                        
                                        completed_samples = len(completed_sample_ids)
                                        total_samples = running_tasks[task_id].get("total_samples", sample_count)
                                        if total_samples > 0:
                                            completed_samples = min(completed_samples, total_samples)
                                            running_tasks[task_id]["current_progress"] = completed_samples
                                            if completed_samples >= total_samples and running_tasks[task_id].get("status") == "running":
                                                running_tasks[task_id]["progress_percent"] = 99
                                            else:
                                                running_tasks[task_id]["progress_percent"] = int((completed_samples / total_samples) * 100)
                                            print(f"📊 定期进度更新: {completed_samples}/{total_samples} ({running_tasks[task_id]['progress_percent']}%)")
                                except Exception as e:
                                    pass  # 忽略错误，避免影响主流程
                
                process.wait()
                
                if process.returncode == 0:
                    running_tasks[task_id]["status"] = "completed"
                    # 🚀 修复：任务完成时，确保进度显示100%
                    if "total_samples" in running_tasks[task_id]:
                        running_tasks[task_id]["current_progress"] = running_tasks[task_id]["total_samples"]
                        running_tasks[task_id]["progress_percent"] = 100
                    running_tasks[task_id]["output"] += f"\n✅ 核心系统执行完成（处理了 {sample_count} 个样本）"
                else:
                    running_tasks[task_id]["status"] = "failed"
                    running_tasks[task_id]["output"] += f"\n❌ 核心系统执行失败（退出码: {process.returncode}）"
                    
            except Exception as e:
                running_tasks[task_id]["status"] = "failed"
                running_tasks[task_id]["output"] += f"\n❌ 执行异常: {str(e)}"
            finally:
                running_tasks[task_id]["end_time"] = time.time()
                if "process" in running_tasks[task_id]:
                    running_tasks[task_id]["process"] = None
        
        # 初始化任务状态
        running_tasks[task_id] = {
            "type": "core_system",
            "status": "starting",
            "process": None,
            "start_time": time.time(),
            "end_time": None,
            "output": "",
            "sample_count": sample_count,
            "current_progress": 0,  # 🚀 新增：当前进度
            "total_samples": sample_count,  # 🚀 新增：总样本数
            "progress_percent": 0  # 🚀 新增：进度百分比
        }
        
        # 启动后台线程
        thread = threading.Thread(target=run_script, daemon=True)
        thread.start()
        
        response = jsonify({
            "success": True,
            "task_id": task_id,
            "message": f"核心系统已启动，正在处理 {sample_count} 个样本",
            "sample_count": sample_count
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        error_response = jsonify({"error": str(e)})
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500


@app.route('/api/evaluation/run', methods=['POST', 'OPTIONS'])
def run_evaluation():
    # 🚀 修复：处理OPTIONS预检请求
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    """🚀 改进：运行评测脚本（异步执行，返回任务ID）"""
    try:
        if not EVALUATION_SCRIPT.exists():
            error_response = jsonify({"error": f"评测脚本不存在: {EVALUATION_SCRIPT}"})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 404
        
        # 🚀 修复：确保脚本有执行权限
        import stat
        script_stat = EVALUATION_SCRIPT.stat()
        if not (script_stat.st_mode & stat.S_IEXEC):
            EVALUATION_SCRIPT.chmod(script_stat.st_mode | stat.S_IEXEC)
        
        # 🚀 改进：生成任务ID
        global task_counter
        task_counter += 1
        task_id = f"eval_{task_counter}_{int(time.time())}"
        
        # 🚀 改进：在后台线程中运行，并跟踪状态
        import threading
        
        def run_script():
            try:
                running_tasks[task_id]["status"] = "running"
                running_tasks[task_id]["output"] = "开始运行评测系统...\n"
                print(f"🚀 评测任务 {task_id} 开始运行")
                
                # 🚀 修复：确保使用项目根目录的.venv环境
                # bash脚本会自动激活.venv，但我们需要确保环境变量正确传递
                env = os.environ.copy()
                # 确保PATH包含项目根目录的.venv（如果存在）
                venv_bin = ROOT_DIR / ".venv" / "bin"
                if venv_bin.exists():
                    current_path = env.get("PATH", "")
                    venv_path = str(venv_bin)
                    if venv_path not in current_path:
                        env["PATH"] = f"{venv_path}:{current_path}"
                
                script_path = str(EVALUATION_SCRIPT.absolute())
                print(f"📝 评测脚本路径: {script_path}")
                print(f"📝 脚本是否存在: {EVALUATION_SCRIPT.exists()}")
                
                # 🚀 修复：创建新进程组，以便可以终止所有子进程
                process = subprocess.Popen(
                    ["bash", script_path],
                    cwd=str(ROOT_DIR.absolute()),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env=env,  # 🚀 修复：使用修改后的环境变量
                    preexec_fn=os.setsid  # 🚀 修复：创建新进程组，以便可以终止所有子进程
                )
                
                running_tasks[task_id]["process"] = process
                print(f"✅ 评测进程已启动，PID: {process.pid}")
                
                # 实时读取输出
                output_buffer = ""
                line_count = 0
                last_output_time = time.time()
                
                # 🚀 修复：使用超时机制，避免进程卡住
                import threading
                
                def read_output():
                    nonlocal output_buffer, line_count, last_output_time
                    try:
                        if process.stdout:
                            for line in iter(process.stdout.readline, ''):
                                if line:
                                    output_buffer += line
                                    line_count += 1
                                    last_output_time = time.time()
                                    running_tasks[task_id]["output"] += line
                                    if len(running_tasks[task_id]["output"]) > 50000:  # 限制输出长度
                                        running_tasks[task_id]["output"] = running_tasks[task_id]["output"][-25000:]
                                    # 🚀 调试：输出关键日志行
                                    if any(keyword in line.lower() for keyword in ["完成", "error", "失败", "未找到", "警告", "评测完成"]):
                                        print(f"📊 评测输出: {line.strip()}")
                    except Exception as e:
                        print(f"⚠️ 读取输出异常: {e}")
                
                # 在单独线程中读取输出
                output_thread = threading.Thread(target=read_output, daemon=True)
                output_thread.start()
                
                # 等待进程结束，但设置超时检查
                max_wait_time = 3600  # 最多等待1小时
                start_wait_time = time.time()
                
                while process.poll() is None:
                    # 检查是否超时
                    elapsed = time.time() - start_wait_time
                    if elapsed > max_wait_time:
                        print(f"⚠️ 评测任务 {task_id} 超时（超过{max_wait_time}秒），终止进程")
                        # 🚀 修复：终止进程组
                        try:
                            pgid = os.getpgid(process.pid)
                            os.killpg(pgid, signal.SIGTERM)
                            time.sleep(2)
                            if process.poll() is None:
                                os.killpg(pgid, signal.SIGKILL)
                        except (OSError, ProcessLookupError):
                            # 如果无法获取进程组，尝试直接终止进程
                            process.terminate()
                            time.sleep(2)
                            if process.poll() is None:
                                process.kill()
                        running_tasks[task_id]["status"] = "failed"
                        running_tasks[task_id]["output"] += f"\n❌ 评测任务超时（超过{max_wait_time}秒）"
                        return
                    
                    # 检查是否有输出（如果超过5分钟没有输出，可能卡住了）
                    if time.time() - last_output_time > 300 and line_count > 0:
                        print(f"⚠️ 评测任务 {task_id} 超过5分钟没有输出，可能卡住了（已运行{elapsed:.0f}秒）")
                        # 不立即终止，继续等待
                    
                    time.sleep(1)
                
                # 等待输出线程完成（最多等待5秒）
                output_thread.join(timeout=5)
                
                return_code = process.returncode
                print(f"📊 评测进程结束，退出码: {return_code}，总耗时: {time.time() - start_wait_time:.1f}秒")
                
                # 🚀 调试：如果失败，输出最后几行输出
                if return_code != 0:
                    output_lines = output_buffer.split('\n')
                    if len(output_lines) > 5:
                        print(f"📊 最后5行输出:\n" + '\n'.join(output_lines[-5:]))
                
                if return_code == 0:
                    running_tasks[task_id]["status"] = "completed"
                    running_tasks[task_id]["output"] += "\n✅ 评测系统执行完成\n"
                    
                    # 读取评测报告
                    report_content = ""
                    if EVALUATION_REPORT.exists():
                        with open(EVALUATION_REPORT, 'r', encoding='utf-8') as f:
                            report_content = f.read()
                    
                    # 🚀 改进：解析报告中的关键指标和结构化数据
                    accuracy = 0.0
                    success_rate = 0.0
                    avg_time = 0.0
                    sample_count = 0
                    analysis_data = {}
                    
                    # 基本统计
                    accuracy_match = re.search(r'平均准确率[：:]\s*([\d.]+)%', report_content)
                    if accuracy_match:
                        accuracy = float(accuracy_match.group(1))
                    
                    success_match = re.search(r'样本成功率[：:]\s*([\d.]+)%', report_content)
                    if success_match:
                        success_rate = float(success_match.group(1))
                    
                    time_match = re.search(r'平均推理时间[：:]\s*([\d.]+)', report_content)
                    if time_match:
                        avg_time = float(time_match.group(1))
                    
                    count_match = re.search(r'样本数量[：:]\s*(\d+)', report_content)
                    if count_match:
                        sample_count = int(count_match.group(1))
                    
                    # 🚀 新增：解析结构化数据用于分析报告
                    # FRAMES评测基准指标
                    frames_data = {}
                    frames_accuracy_match = re.search(r'平均准确率[：:]\s*([\d.]+)%', report_content)
                    if frames_accuracy_match:
                        frames_data['average_accuracy'] = float(frames_accuracy_match.group(1))
                    frames_steps_match = re.search(r'平均推理步骤[：:]\s*([\d.]+)', report_content)
                    if frames_steps_match:
                        frames_data['average_steps'] = float(frames_steps_match.group(1))
                    frames_innovation_match = re.search(r'创新性分数[：:]\s*([\d.]+)', report_content)
                    if frames_innovation_match:
                        frames_data['innovation_score'] = float(frames_innovation_match.group(1))
                    
                    # 系统智能化程度
                    intelligence_data = {}
                    intelligence_match = re.search(r'整体智能分数[：:]\s*([\d.]+)', report_content)
                    if intelligence_match:
                        intelligence_data['overall'] = float(intelligence_match.group(1))
                    ai_algorithm_match = re.search(r'AI算法分数[：:]\s*([\d.]+)', report_content)
                    if ai_algorithm_match:
                        intelligence_data['ai_algorithm'] = float(ai_algorithm_match.group(1))
                    learning_match = re.search(r'学习能力分数[：:]\s*([\d.]+)', report_content)
                    if learning_match:
                        intelligence_data['learning'] = float(learning_match.group(1))
                    reasoning_match = re.search(r'推理能力分数[：:]\s*([\d.]+)', report_content)
                    if reasoning_match:
                        intelligence_data['reasoning'] = float(reasoning_match.group(1))
                    
                    # 系统性能
                    performance_data = {}
                    perf_time_match = re.search(r'平均处理时间[：:]\s*([\d.]+)', report_content)
                    if perf_time_match:
                        performance_data['avg_time'] = float(perf_time_match.group(1))
                    max_time_match = re.search(r'最大处理时间[：:]\s*([\d.]+)', report_content)
                    if max_time_match:
                        performance_data['max_time'] = float(max_time_match.group(1))
                    min_time_match = re.search(r'最小处理时间[：:]\s*([\d.]+)', report_content)
                    if min_time_match:
                        performance_data['min_time'] = float(min_time_match.group(1))
                    cache_match = re.search(r'缓存命中率[：:]\s*([\d.]+)%', report_content)
                    if cache_match:
                        performance_data['cache_hit_rate'] = float(cache_match.group(1))
                    
                    # 自我学习程度
                    learning_data = {}
                    ml_learning_match = re.search(r'ML学习分数[：:]\s*([\d.]+)', report_content)
                    if ml_learning_match:
                        learning_data['ml_score'] = float(ml_learning_match.group(1))
                    rl_learning_match = re.search(r'RL学习分数[：:]\s*([\d.]+)', report_content)
                    if rl_learning_match:
                        learning_data['rl_score'] = float(rl_learning_match.group(1))
                    self_learning_match = re.search(r'自我学习分数[：:]\s*([\d.]+)', report_content)
                    if self_learning_match:
                        learning_data['self_learning_score'] = float(self_learning_match.group(1))
                    
                    analysis_data = {
                        'frames': frames_data,
                        'intelligence': intelligence_data,
                        'performance': performance_data,
                        'learning': learning_data
                    }
                    
                    running_tasks[task_id]["report"] = report_content
                    running_tasks[task_id]["accuracy"] = accuracy
                    running_tasks[task_id]["success_rate"] = success_rate
                    running_tasks[task_id]["avg_time"] = avg_time
                    running_tasks[task_id]["sample_count"] = sample_count
                    running_tasks[task_id]["analysis"] = analysis_data
                    print(f"✅ 评测任务 {task_id} 完成")
                else:
                    running_tasks[task_id]["status"] = "failed"
                    running_tasks[task_id]["output"] += f"\n❌ 评测系统执行失败（退出码: {return_code}）"
                    print(f"❌ 评测任务 {task_id} 失败，退出码: {return_code}")
                    # 🚀 调试：输出最后几行输出，帮助诊断问题
                    output_lines = running_tasks[task_id]["output"].split('\n')
                    if len(output_lines) > 10:
                        print(f"📊 最后10行输出:\n" + '\n'.join(output_lines[-10:]))
                    
            except Exception as e:
                print(f"❌ 评测任务 {task_id} 执行异常: {str(e)}")
                import traceback
                error_trace = traceback.format_exc()
                print(f"❌ 异常堆栈:\n{error_trace}")
                running_tasks[task_id]["status"] = "failed"
                running_tasks[task_id]["output"] += f"\n❌ 执行异常: {str(e)}"
                running_tasks[task_id]["error"] = error_trace
            finally:
                running_tasks[task_id]["end_time"] = time.time()
                print(f"📊 评测任务 {task_id} 结束时间: {running_tasks[task_id]['end_time']}")
                if "process" in running_tasks[task_id]:
                    running_tasks[task_id]["process"] = None
        
        # 初始化任务状态
        running_tasks[task_id] = {
            "type": "evaluation",
            "status": "starting",
            "process": None,
            "start_time": time.time(),
            "end_time": None,
            "output": "",
            "report": None,
            "accuracy": 0.0,
            "success_rate": 0.0,
            "avg_time": 0.0,
            "sample_count": 0
        }
        
        # 启动后台线程
        thread = threading.Thread(target=run_script, daemon=True)
        thread.start()
        
        response = jsonify({
            "success": True,
            "task_id": task_id,
            "message": "评测系统已启动"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        import traceback
        error_response = jsonify({
            "error": str(e),
            "details": traceback.format_exc()
        })
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500


@app.route('/api/tasks/<task_id>', methods=['GET', 'OPTIONS'])
def get_task_status(task_id):
    """🚀 新增：获取任务状态"""
    # 🚀 修复：处理OPTIONS预检请求
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    try:
        if task_id not in running_tasks:
            error_response = jsonify({"error": "任务不存在"})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 404
        
        task = running_tasks[task_id]
        duration = None
        if task.get("end_time"):
            duration = task["end_time"] - task["start_time"]
        elif task.get("start_time"):
            duration = time.time() - task["start_time"]
        
        result = {
            "task_id": task_id,
            "type": task["type"],
            "status": task["status"],
            "start_time": task["start_time"],
            "end_time": task.get("end_time"),
            "duration": duration,
            "output": task.get("output", "")[-5000:] if task.get("output") else ""  # 只返回最后5000字符
        }
        
        # 如果是评测任务且已完成，添加报告信息
        if task["type"] == "evaluation" and task["status"] == "completed":
            result.update({
                "report": task.get("report", ""),
                "accuracy": task.get("accuracy", 0.0),
                "success_rate": task.get("success_rate", 0.0),
                "avg_time": task.get("avg_time", 0.0),
                "sample_count": task.get("sample_count", 0),
                "analysis": task.get("analysis", {})  # 🚀 添加分析数据
            })
        elif task["type"] == "core_system":
            result["sample_count"] = task.get("sample_count", 0)
            # 🚀 新增：返回进度信息
            result["current_progress"] = task.get("current_progress", 0)
            result["total_samples"] = task.get("total_samples", task.get("sample_count", 0))
            result["progress_percent"] = task.get("progress_percent", 0)
        
        response = jsonify(result)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        error_response = jsonify({"error": str(e)})
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500


@app.route('/api/tasks/<task_id>/cancel', methods=['POST', 'OPTIONS'])
def cancel_task(task_id):
    """🚀 新增：取消任务"""
    # 🚀 修复：处理OPTIONS预检请求
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    try:
        if task_id not in running_tasks:
            error_response = jsonify({"error": "任务不存在"})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 404
        
        task = running_tasks[task_id]
        if task["status"] not in ["starting", "running"]:
            error_response = jsonify({"error": "任务无法取消（已完成或已失败）"})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400
        
        # 🚀 修复：终止进程及其所有子进程
        if task.get("process"):
            try:
                process = task["process"]
                # 获取进程组ID（如果进程还在运行）
                if process.poll() is None:
                    try:
                        # 尝试使用进程组终止所有子进程
                        pgid = os.getpgid(process.pid)
                        os.killpg(pgid, signal.SIGTERM)
                        print(f"✅ 已发送SIGTERM信号到进程组 {pgid} (PID: {process.pid})")
                    except (OSError, ProcessLookupError) as e:
                        # 如果无法获取进程组，尝试直接终止进程
                        print(f"⚠️ 无法获取进程组，尝试直接终止进程: {e}")
                        try:
                            process.terminate()
                        except Exception as e2:
                            print(f"⚠️ 终止进程失败: {e2}")
                    
                    # 等待进程终止（最多等待2秒）
                    waited = 0
                    while process.poll() is None and waited < 2:
                        time.sleep(0.1)
                        waited += 0.1
                    
                    if process.poll() is None:
                        # 如果进程没有在2秒内终止，强制杀死
                        print(f"⚠️ 进程未在2秒内终止，强制杀死")
                        try:
                            pgid = os.getpgid(process.pid)
                            os.killpg(pgid, signal.SIGKILL)
                            print(f"✅ 已发送SIGKILL信号到进程组 {pgid}")
                        except (OSError, ProcessLookupError) as e:
                            # 如果无法获取进程组，尝试直接杀死进程
                            try:
                                process.kill()
                                print(f"✅ 已强制杀死进程")
                            except Exception as e2:
                                print(f"⚠️ 强制杀死进程失败: {e2}")
                    else:
                        print(f"✅ 进程已正常终止 (退出码: {process.returncode})")
                else:
                    print(f"ℹ️ 进程已结束 (退出码: {process.returncode})")
            except Exception as e:
                print(f"❌ 终止进程失败: {e}")
                import traceback
                traceback.print_exc()
        
        task["status"] = "cancelled"
        task["end_time"] = time.time()
        task["output"] += "\n⚠️ 任务已被取消\n"
        
        response = jsonify({
            "success": True,
            "message": "任务已取消"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        error_response = jsonify({"error": str(e)})
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500


@app.route('/api/generate_tensorboard_logs', methods=['POST', 'OPTIONS'])
def generate_tensorboard_logs():
    """🚀 新增：生成 TensorBoard 日志并启动 TensorBoard 服务器"""
    global tensorboard_process
    
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    
    try:
        data = request.get_json()
        sample_id = data.get('sample_id')
        steps = data.get('steps', [])
        
        if not steps:
            return jsonify({"success": False, "error": "没有推理步骤数据"}), 400
        
        # 创建样本特定的日志目录
        sample_log_dir = TENSORBOARD_LOG_DIR / f"sample_{sample_id}"
        sample_log_dir.mkdir(exist_ok=True)
        
        # 生成 TensorBoard 日志文件
        # 使用 tensorboard 的 protobuf 模块
        try:
            # pylint: disable=import-error
            # TensorBoard 2.x 版本的正确导入方式
            import importlib
            import struct
            import time as time_module
            import socket
            
            # 尝试多种导入方式
            try:
                # 方式1: 从 tensorboard.compat.proto 导入
                event_pb2 = importlib.import_module('tensorboard.compat.proto.event_pb2')
                summary_pb2 = importlib.import_module('tensorboard.compat.proto.summary_pb2')
            except ImportError:
                try:
                    # 方式2: 从 tensorboard.summary.writer 导入
                    writer_module = importlib.import_module('tensorboard.summary.writer')
                    event_pb2 = writer_module.event_pb2
                    summary_pb2 = writer_module.summary_pb2
                except (ImportError, AttributeError):
                    # 方式3: 直接导入
                    import tensorboard.compat.proto.event_pb2 as event_pb2  # type: ignore
                    import tensorboard.compat.proto.summary_pb2 as summary_pb2  # type: ignore
            
            # 尝试导入文本摘要功能
            try:
                from tensorboard.plugins.text import summary as text_summary
                has_text_summary = True
            except ImportError:
                has_text_summary = False
            
            # 尝试导入直方图摘要功能
            try:
                from tensorboard.plugins.histogram import summary as histogram_summary
                has_histogram_summary = True
            except ImportError:
                has_histogram_summary = False
            
            # 尝试导入图像摘要功能
            try:
                from tensorboard.plugins.image import summary as image_summary
                import io
                import base64
                from PIL import Image, ImageDraw, ImageFont
                has_image_summary = True
            except ImportError:
                has_image_summary = False
            
            # 创建事件文件
            event_file = sample_log_dir / "events.out.tfevents.0000000000"
            
            with open(event_file, 'wb') as f:
                # 为每个步骤创建事件
                for step_index, step in enumerate(steps):
                    # 创建事件
                    event = event_pb2.Event()
                    event.wall_time = step.get('timestamp', time_module.time())  # type: ignore
                    event.step = step_index  # type: ignore
                    
                    # 创建摘要
                    summary = summary_pb2.Summary()
                    
                    # 步骤基本信息
                    step_type = step.get('type', 'unknown')
                    step_number = step.get('number', step_index + 1)
                    step_description = step.get('description', '')
                    
                    # 1. 记录步骤类型（使用更清晰的数值映射）
                    step_type_map = {
                        'evidence': 1.0,
                        'reasoning': 2.0,
                        'answer': 3.0,
                        'validation': 4.0,
                        'search': 5.0,
                        'analysis': 6.0,
                        'query_analysis': 1.5,
                        'evidence_gathering': 1.2,
                        'logical_deduction': 2.5,
                        'answer_synthesis': 3.5,
                        'verification': 4.2,
                        'fact_checking': 4.5,
                        'pattern_recognition': 6.2,
                        'causal_reasoning': 2.8,
                        'analogical_reasoning': 2.3,
                        'mathematical_reasoning': 2.6,
                        'pattern_analysis': 6.5
                    }
                    step_type_value = step_type_map.get(step_type.lower(), 0.0)
                    summary_value = summary.value.add()  # type: ignore
                    summary_value.tag = f"推理流程/步骤类型"
                    summary_value.simple_value = step_type_value
                    
                    # 2. 记录步骤编号（用于查看步骤顺序）
                    summary_value = summary.value.add()  # type: ignore
                    summary_value.tag = f"推理流程/步骤编号"
                    summary_value.simple_value = float(step_number)
                    
                    # 3. 记录置信度（如果有）
                    if step.get('confidence') is not None:
                        confidence = float(step.get('confidence', 0.0))
                        summary_value = summary.value.add()  # type: ignore
                        summary_value.tag = f"推理质量/置信度"
                        summary_value.simple_value = confidence
                    
                    # 4. 记录耗时（如果有，转换为秒）
                    if step.get('duration') is not None:
                        duration = float(step.get('duration', 0.0))
                        # 如果 duration 是毫秒，转换为秒
                        if duration > 1000:
                            duration = duration / 1000.0
                        summary_value = summary.value.add()  # type: ignore
                        summary_value.tag = f"性能指标/步骤耗时(秒)"
                        summary_value.simple_value = duration
                    
                    # 5. 记录步骤描述作为文本摘要（如果支持）
                    if step_description and has_text_summary:
                        try:
                            # 截取描述的前2000字符（增加长度，确保内容完整）
                            desc_text = str(step_description)[:2000]
                            # 创建文本摘要标题
                            text_title = f"步骤 {step_number} ({step_type})"
                            # 创建完整的文本内容（标题 + 描述）
                            full_text = f"{text_title}\n\n{desc_text}"
                            
                            # 创建文本摘要（text_pb返回的是Summary对象，需要提取value）
                            text_summary_obj = text_summary.text_pb(
                                text_title,
                                full_text
                            )
                            
                            # 将文本摘要的value添加到主summary中
                            # text_pb返回的Summary对象包含value列表，需要逐个复制
                            text_count = 0
                            # 🚀 修复：使用getattr避免linter错误，Summary对象确实有value属性
                            text_summary_values = getattr(text_summary_obj, 'value', [])
                            for text_value in text_summary_values:
                                new_value = summary.value.add()  # type: ignore
                                new_value.CopyFrom(text_value)
                                # 修改tag，使其更清晰（使用更简单的tag名称，避免特殊字符）
                                new_value.tag = f"推理步骤/步骤_{step_number}_{step_type}"
                                text_count += 1
                            
                            # 记录成功信息（使用print，因为这是API调用，日志可能看不到）
                            print(f"✅ [TensorBoard] 成功记录文本摘要: 步骤{step_number}, 类型{step_type}, 长度{len(desc_text)}, value数量{text_count}")
                            app.logger.info(f"✅ 成功记录文本摘要: 步骤{step_number}, 类型{step_type}, 长度{len(desc_text)}")
                        except Exception as e:
                            # 记录错误信息，便于调试
                            import traceback
                            error_msg = f"记录文本摘要失败: {e}\n{traceback.format_exc()}"
                            print(f"❌ [TensorBoard] {error_msg}")
                            app.logger.warning(error_msg)
                            # 不抛出异常，继续处理其他数据
                    elif step_description and not has_text_summary:
                        print(f"⚠️ [TensorBoard] 文本摘要插件不可用，跳过步骤{step_number}的描述")
                    elif not step_description:
                        print(f"⚠️ [TensorBoard] 步骤{step_number}没有描述文本，跳过文本摘要")
                    
                    # 6. 记录累积步骤数（用于查看推理深度）
                    summary_value = summary.value.add()  # type: ignore
                    summary_value.tag = f"推理流程/累积步骤数"
                    summary_value.simple_value = float(step_index + 1)
                    
                    # 7. 记录步骤进度百分比
                    if len(steps) > 0:
                        progress = (step_index + 1) / len(steps) * 100.0
                        summary_value = summary.value.add()  # type: ignore
                        summary_value.tag = f"推理流程/进度百分比"
                        summary_value.simple_value = progress
                    
                    event.summary.CopyFrom(summary)  # type: ignore
                    
                    # 写入事件
                    event_str = event.SerializeToString()  # type: ignore
                    f.write(struct.pack('Q', len(event_str)))
                    f.write(event_str)
                    f.write(struct.pack('I', 0x80000000 | 0x00000001))  # CRC32
            
            # 启动 TensorBoard 服务器（如果还没有启动）
            if tensorboard_process is None or tensorboard_process.poll() is not None:
                # 启动 TensorBoard
                tensorboard_process = subprocess.Popen(
                    ['tensorboard', '--logdir', str(TENSORBOARD_LOG_DIR), '--port', str(tensorboard_port), '--host', '0.0.0.0'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setsid if hasattr(os, 'setsid') else None
                )
                
                # 等待并检查服务器是否启动成功
                max_wait_time = 10  # 最多等待10秒
                wait_interval = 0.5  # 每0.5秒检查一次
                waited_time = 0
                server_ready = False
                
                while waited_time < max_wait_time:
                    time.sleep(wait_interval)
                    waited_time += wait_interval
                    
                    # 检查进程是否还在运行
                    if tensorboard_process.poll() is not None:
                        # 进程已退出，读取错误信息
                        stderr_output = tensorboard_process.stderr.read().decode('utf-8', errors='ignore') if tensorboard_process.stderr else ''
                        raise Exception(f"TensorBoard 进程启动失败: {stderr_output}")
                    
                    # 检查端口是否可访问
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        result = sock.connect_ex(('localhost', tensorboard_port))
                        sock.close()
                        if result == 0:
                            server_ready = True
                            break
                    except Exception:
                        pass
                
                if not server_ready:
                    # 如果服务器未就绪，尝试读取错误信息
                    stderr_output = ''
                    if tensorboard_process.stderr:
                        try:
                            stderr_output = tensorboard_process.stderr.read().decode('utf-8', errors='ignore')
                        except Exception:
                            pass
                    raise Exception(f"TensorBoard 服务器启动超时。错误信息: {stderr_output}")
            
            tensorboard_url = f"http://localhost:{tensorboard_port}"
            
            response = jsonify({
                "success": True,
                "tensorboard_url": tensorboard_url,
                "log_dir": str(sample_log_dir)
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
        except ImportError:
            # 如果没有安装 tensorboard，返回错误
            return jsonify({
                "success": False,
                "error": "TensorBoard 未安装。请运行: pip install tensorboard"
            }), 500
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"生成 TensorBoard 日志失败: {str(e)}"
            }), 500
            
    except Exception as e:
        error_response = jsonify({"success": False, "error": str(e)})
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500


@app.route('/api/evaluation/result', methods=['GET', 'OPTIONS'])
def get_evaluation_result():
    """获取最新的评测结果"""
    # 🚀 修复：处理OPTIONS预检请求
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    try:
        if not EVALUATION_REPORT.exists():
            error_response = jsonify({"error": "评测报告不存在"})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 404
        
        with open(EVALUATION_REPORT, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        # 解析关键指标（同上）
        accuracy = 0.0
        success_rate = 0.0
        avg_time = 0.0
        sample_count = 0
        
        accuracy_match = re.search(r'准确率[：:]\s*([\d.]+)%', report_content)
        if accuracy_match:
            accuracy = float(accuracy_match.group(1))
        
        success_match = re.search(r'样本成功率[：:]\s*([\d.]+)%', report_content)
        if success_match:
            success_rate = float(success_match.group(1))
        
        time_match = re.search(r'平均耗时[：:]\s*([\d.]+)', report_content)
        if time_match:
            avg_time = float(time_match.group(1))
        
        count_match = re.search(r'样本数量[：:]\s*(\d+)', report_content)
        if count_match:
            sample_count = int(count_match.group(1))
        
        response = jsonify({
            "report": report_content,
            "accuracy": accuracy,
            "success_rate": success_rate,
            "avg_time": avg_time,
            "sample_count": sample_count
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        error_response = jsonify({"error": str(e)})
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500


# ==================== MCP管理API ====================

def proxy_to_rangen_api(endpoint, method='GET', data=None, files=None, headers=None):
    """转发请求到RANGEN主API"""
    try:
        url = f"{RANGEN_API_BASE}{endpoint}"
        
        # 默认headers
        if headers is None:
            headers = {}
        
        # 如果没有Content-Type头，则根据data类型设置
        if 'Content-Type' not in headers:
            if files:
                # 文件上传时，requests会自动设置multipart/form-data
                pass
            elif data is not None and not isinstance(data, (str, bytes)):
                headers['Content-Type'] = 'application/json'
        
        request_kwargs = {
            'url': url,
            'headers': headers,
            'timeout': 30
        }
        
        method_upper = method.upper()
        
        if method_upper == 'GET':
            response = requests.get(**request_kwargs)
        elif method_upper == 'POST':
            if files:
                request_kwargs['files'] = files
                if data:
                    request_kwargs['data'] = data
            elif data is not None:
                if isinstance(data, (str, bytes)):
                    request_kwargs['data'] = data
                else:
                    request_kwargs['json'] = data
            response = requests.post(**request_kwargs)
        elif method_upper == 'PUT':
            if data is not None:
                if isinstance(data, (str, bytes)):
                    request_kwargs['data'] = data
                else:
                    request_kwargs['json'] = data
            response = requests.put(**request_kwargs)
        elif method_upper == 'DELETE':
            if data is not None:
                if isinstance(data, (str, bytes)):
                    request_kwargs['data'] = data
                else:
                    request_kwargs['json'] = data
            response = requests.delete(**request_kwargs)
        else:
            return jsonify({"error": f"Unsupported method: {method}"}), 400
        
        # 返回原始响应
        return Response(
            response.content,
            status=response.status_code,
            headers=dict(response.headers)
        )
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to connect to RANGEN API: {str(e)}"}), 503
    except Exception as e:
        return jsonify({"error": f"Internal error: {str(e)}"}), 500


@app.route('/api/mcp/status', methods=['GET', 'OPTIONS'])
def get_mcp_status():
    """获取MCP系统状态"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    return proxy_to_rangen_api('/mcp/status', 'GET')


@app.route('/api/mcp/servers', methods=['GET', 'OPTIONS'])
def get_mcp_servers():
    """获取所有MCP服务器状态"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    return proxy_to_rangen_api('/mcp/servers', 'GET')


@app.route('/api/mcp/servers/<server_name>/<action>', methods=['POST', 'OPTIONS'])
def manage_mcp_server(server_name, action):
    """管理MCP服务器（启动、停止、重启）"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    return proxy_to_rangen_api(f'/mcp/servers/{server_name}/{action}', 'POST', request.json)


@app.route('/api/mcp/tools', methods=['GET', 'OPTIONS'])
def get_mcp_tools():
    """获取所有MCP工具"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    return proxy_to_rangen_api('/mcp/tools', 'GET')


@app.route('/api/mcp/config', methods=['GET', 'OPTIONS'])
def get_mcp_config():
    """获取MCP配置"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    return proxy_to_rangen_api('/mcp/config', 'GET')


@app.route('/api/mcp/health', methods=['GET', 'OPTIONS'])
def get_mcp_health():
    """获取MCP健康状态"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    return proxy_to_rangen_api('/mcp/health', 'GET')


# ==================== 外部集成API ====================

@app.route('/api/external/integrations', methods=['GET', 'OPTIONS'])
def get_external_integrations():
    """获取所有外部集成"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    return proxy_to_rangen_api('/api/v1/external/integrations', 'GET')

@app.route('/api/external/mcp/add', methods=['POST', 'OPTIONS'])
def add_external_mcp():
    """添加外部MCP端点"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    return proxy_to_rangen_api('/api/v1/external/mcp/add', 'POST', request.json)

@app.route('/api/external/mcp/connect/<name>', methods=['POST', 'OPTIONS'])
def connect_external_mcp(name):
    """连接外部MCP端点"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    return proxy_to_rangen_api(f'/api/v1/external/mcp/connect/{name}', 'POST', request.json if request.json else {})

@app.route('/api/external/mcp/tools/<endpoint_name>', methods=['GET', 'OPTIONS'])
def list_external_mcp_tools(endpoint_name):
    """列出外部MCP服务器工具"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    return proxy_to_rangen_api(f'/api/v1/external/mcp/tools/{endpoint_name}', 'GET')

@app.route('/api/external/openai/import', methods=['POST', 'OPTIONS'])
def import_openai_agent():
    """导入OpenAI GPTs Agent"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    return proxy_to_rangen_api('/api/v1/external/openai/import', 'POST', request.json)

@app.route('/api/external/github/import', methods=['POST', 'OPTIONS'])
def import_github_copilot():
    """导入GitHub Copilot Agent"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    return proxy_to_rangen_api('/api/v1/external/github/import', 'POST', request.json)

@app.route('/api/external/custom-api/add', methods=['POST', 'OPTIONS'])
def add_custom_api():
    """添加自定义API"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    return proxy_to_rangen_api('/api/v1/external/custom-api/add', 'POST', request.json)

@app.route('/api/external/import/yaml', methods=['POST', 'OPTIONS'])
def import_yaml():
    """从YAML文件导入配置"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    # 文件上传需要特殊处理
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    # 直接转发文件到RANGEN API
    files = {'file': (file.filename, file.stream, file.content_type or 'application/x-yaml')}
    
    return proxy_to_rangen_api('/api/v1/external/import/yaml', 'POST', files=files)

@app.route('/api/external/import/json', methods=['POST', 'OPTIONS'])
def import_json():
    """从JSON文件导入配置"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    # 文件上传需要特殊处理
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    # 直接转发文件到RANGEN API
    files = {'file': (file.filename, file.stream, file.content_type or 'application/json')}
    
    return proxy_to_rangen_api('/api/v1/external/import/json', 'POST', files=files)

@app.route('/api/external/integrations/<integration_id>', methods=['DELETE', 'OPTIONS'])
def remove_external_integration(integration_id):
    """移除外部集成"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    return proxy_to_rangen_api(f'/api/v1/external/integrations/{integration_id}', 'DELETE')


# ==================== 工具管理API ====================

@app.route('/api/tools', methods=['GET', 'OPTIONS'])
def get_tools():
    """获取工具列表（代理到RANGEN主API）"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    # 获取查询参数
    status = request.args.get('status', None)
    page = request.args.get('page', None)
    page_size = request.args.get('page_size', None)
    
    # 构建端点URL
    endpoint = '/api/v1/tools'
    params = []
    if status:
        params.append(f'status={status}')
    if page:
        params.append(f'page={page}')
    if page_size:
        params.append(f'page_size={page_size}')
    
    if params:
        endpoint = f'{endpoint}?{"&".join(params)}'
    
    return proxy_to_rangen_api(endpoint, 'GET')

@app.route('/api/tools/<tool_id>', methods=['GET', 'OPTIONS'])
def get_tool_detail(tool_id):
    """获取工具详情（代理到RANGEN主API）"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    # 构建端点URL
    endpoint = f'/api/v1/tools/{tool_id}'
    
    return proxy_to_rangen_api(endpoint, 'GET')

@app.route('/api/tools/internal', methods=['GET', 'OPTIONS'])
def get_internal_tools():
    """获取内部工具列表"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    # 这里可以返回内部工具列表
    # 由于内部工具列表可能没有直接API，我们可以返回一个静态列表
    # 或者从主API获取，这里先返回示例数据
    internal_tools = [
        {"name": "rag_tool", "description": "检索增强生成工具", "category": "retrieval"},
        {"name": "knowledge_retrieval", "description": "知识检索工具", "category": "retrieval"},
        {"name": "search", "description": "搜索工具", "category": "retrieval"},
        {"name": "web_search", "description": "网页搜索工具", "category": "retrieval"},
        {"name": "real_search", "description": "真实网络搜索工具", "category": "retrieval"},
        {"name": "reasoning", "description": "推理工具", "category": "reasoning"},
        {"name": "answer_generation", "description": "答案生成工具", "category": "generation"},
        {"name": "citation", "description": "引用工具", "category": "generation"},
        {"name": "calculator", "description": "计算器工具", "category": "utility"},
        {"name": "multimodal", "description": "多模态处理工具", "category": "utility"},
        {"name": "browser", "description": "浏览器自动化工具", "category": "utility"},
        {"name": "file_read", "description": "文件读取工具", "category": "utility"}
    ]
    
    response = jsonify({"tools": internal_tools})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


# 🚀 新增：清理 TensorBoard 进程的函数
def cleanup_tensorboard():
    """清理 TensorBoard 进程"""
    global tensorboard_process
    if tensorboard_process is not None:
        try:
            if tensorboard_process.poll() is None:  # 进程还在运行
                if hasattr(os, 'getpgid'):
                    try:
                        pgid = os.getpgid(tensorboard_process.pid)
                        os.killpg(pgid, signal.SIGTERM)
                    except (OSError, ProcessLookupError):
                        tensorboard_process.terminate()
                else:
                    tensorboard_process.terminate()
                # 等待进程结束
                try:
                    tensorboard_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    tensorboard_process.kill()
                tensorboard_process = None
        except Exception as e:
            print(f"⚠️  清理 TensorBoard 进程时出错: {e}")

# 🚀 新增：注册信号处理器，确保退出时清理 TensorBoard
def signal_handler(signum, frame):
    """信号处理器"""
    print("\n🛑 收到退出信号，正在清理...")
    cleanup_tensorboard()
    sys.exit(0)

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    import sys
    import socket
    
    # 🚀 修复：检查端口5000是否被占用（macOS AirPlay服务），如果被占用则使用5001
    def check_port(port):
        """检查端口是否可用"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0  # True表示端口被占用
        except Exception:
            return False
    
    def find_available_port(start_port=5000, max_attempts=3):
        """查找可用端口"""
        for i in range(max_attempts):
            port = start_port + i
            if not check_port(port):
                return port
        # 如果都不可用，返回最后一个尝试的端口（让Flask报错）
        return start_port + max_attempts - 1
    
    # 查找可用端口
    port = find_available_port(5000, 3)
    
    if port != 5000:
        print(f"⚠️  端口 5000 被占用（可能是macOS AirPlay服务），使用端口 {port}")
    
    print(f"🚀 RANGEN前端监控系统后端启动")
    print(f"📁 项目根目录: {ROOT_DIR}")
    print(f"📄 日志文件: {LOG_FILE}")
    print(f"🔍 评测脚本: {EVALUATION_SCRIPT}")
    print(f"🌐 服务地址: http://0.0.0.0:{port}")
    print(f"💡 提示: 如果前端无法连接，请确保前端代理配置指向端口 {port}")
    print(f"💡 提示: 前端代理已配置为默认使用端口 5001")
    print(f"💡 提示: 如果后端运行在端口 {port}，请设置环境变量: export VITE_API_URL=http://localhost:{port}")
    
    try:
        # 使用 atexit 确保退出时清理 TensorBoard
        import atexit
        atexit.register(cleanup_tensorboard)
        
        app.run(host='0.0.0.0', port=port, debug=True)
    except KeyboardInterrupt:
        print("\n🛑 收到中断信号，正在清理...")
        cleanup_tensorboard()
        sys.exit(0)
    except OSError as e:
        if "Address already in use" in str(e):
            # 如果仍然失败，尝试5001
            if port != 5001:
                print(f"⚠️  端口 {port} 启动失败，尝试端口 5001...")
                try:
                    app.run(host='0.0.0.0', port=5001, debug=True)
                except Exception as e2:
                    print(f"❌ 启动失败: {e2}")
                    print(f"💡 请手动指定端口: python app.py --port 5002")
                    sys.exit(1)
            else:
                print(f"❌ 启动失败: {e}")
                sys.exit(1)
        else:
            raise

