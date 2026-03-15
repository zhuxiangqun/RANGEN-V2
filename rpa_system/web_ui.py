"""
RPA系统Web UI界面
使用Flask提供Web界面，支持参数调整、运行控制、报告查看
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from flask import Flask, render_template, request, jsonify, Response, stream_with_context
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    logger.warning("Flask未安装，Web UI功能不可用。请运行: pip install flask flask-cors")

if FLASK_AVAILABLE:
    from .core_controller import RPAController
    from .config import RPA_CONFIG
    
    app = Flask(__name__, 
                template_folder=str(Path(__file__).parent / "templates"),
                static_folder=str(Path(__file__).parent / "static"))
    CORS(app)
else:
    app = None

# 全局控制器实例
controller = None


def init_controller():
    """初始化控制器"""
    global controller
    if controller is None:
        controller = RPAController()


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/status', methods=['GET'])
def get_status():
    """获取系统状态"""
    init_controller()
    status = controller.get_status()
    return jsonify(status)


@app.route('/api/config', methods=['GET'])
def get_config():
    """获取当前配置"""
    init_controller()
    config = controller.state.get("current_config", {})
    return jsonify(config)


@app.route('/api/config', methods=['POST'])
def update_config():
    """更新配置"""
    init_controller()
    data = request.json
    
    sample_count = data.get('sample_count')
    timeout = data.get('timeout')
    
    controller.update_config(
        sample_count=sample_count,
        timeout=timeout
    )
    
    return jsonify({
        "status": "success",
        "message": "配置已更新",
        "config": controller.state.get("current_config", {})
    })


@app.route('/api/run', methods=['POST'])
def start_run():
    """启动运行"""
    init_controller()
    
    if controller.is_running:
        return jsonify({
            "status": "error",
            "message": "系统正在运行中，请等待完成"
        }), 400
    
    data = request.json or {}
    sample_count = data.get('sample_count')
    timeout = data.get('timeout')
    use_frontend_automation = data.get('use_frontend_automation', False)
    headless = data.get('headless', False)
    
    # 在后台任务中运行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    def run_async():
        return loop.run_until_complete(
            controller.run_full_cycle(
                sample_count=sample_count,
                timeout=timeout,
                use_frontend_automation=use_frontend_automation,
                headless=headless
            )
        )
    
    # 启动异步任务
    import threading
    thread = threading.Thread(target=run_async)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "status": "started",
        "message": "运行已启动",
        "run_id": controller.current_run_id,
        "use_frontend_automation": use_frontend_automation
    })


@app.route('/api/run/status', methods=['GET'])
def get_run_status():
    """获取运行状态"""
    init_controller()
    return jsonify({
        "is_running": controller.is_running,
        "current_run_id": controller.current_run_id,
    })


@app.route('/api/reports', methods=['GET'])
def list_reports():
    """列出所有报告"""
    reports_dir = RPA_CONFIG["rpa"]["reports_dir"]
    reports = []
    
    if reports_dir.exists():
        for report_file in sorted(reports_dir.glob("rpa_report_*.json"), 
                                 key=lambda p: p.stat().st_mtime, 
                                 reverse=True):
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                    reports.append({
                        "run_id": report_data.get("run_id"),
                        "start_time": report_data.get("start_time"),
                        "end_time": report_data.get("end_time"),
                        "status": report_data.get("status"),
                        "report_path": str(report_file),
                    })
            except Exception as e:
                logger.error(f"读取报告失败: {report_file}, {e}")
    
    return jsonify({"reports": reports})


@app.route('/api/reports/<run_id>', methods=['GET'])
def get_report(run_id: str):
    """获取指定报告"""
    reports_dir = RPA_CONFIG["rpa"]["reports_dir"]
    report_file = reports_dir / f"rpa_report_{run_id}.json"
    
    if not report_file.exists():
        return jsonify({
            "status": "error",
            "message": "报告不存在"
        }), 404
    
    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        return jsonify(report_data)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"读取报告失败: {e}"
        }), 500


@app.route('/api/logs', methods=['GET'])
def stream_logs():
    """流式传输日志"""
    log_path = RPA_CONFIG["core_system"]["log_path"]
    
    def generate():
        if log_path.exists():
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 读取最后1000行
                lines = f.readlines()
                for line in lines[-1000:]:
                    yield f"data: {json.dumps({'line': line})}\n\n"
        else:
            yield f"data: {json.dumps({'line': '日志文件不存在'})}\n\n"
    
    return Response(stream_with_context(generate()), 
                   mimetype='text/event-stream')


if __name__ == '__main__':
    if not FLASK_AVAILABLE:
        print("错误: Flask未安装，无法启动Web UI")
        print("请运行: pip install flask flask-cors")
        sys.exit(1)
    
    init_controller()
    config = RPA_CONFIG["ui"]
    app.run(
        host=config["host"],
        port=config["port"],
        debug=config["debug"]
    )

