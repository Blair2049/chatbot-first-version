"""
Vercel部署入口文件
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    # 导入Flask应用
    from chatbot_web import app
    
    # 设置生产环境
    app.debug = False
    
    # Vercel需要这个变量来识别Flask应用
    handler = app
    
    print("✅ Flask应用成功导入")
    
except Exception as e:
    print(f"❌ 导入Flask应用失败: {e}")
    
    # 创建一个简单的测试应用
    from flask import Flask, jsonify
    
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return jsonify({"message": "Flask应用正在运行", "error": str(e)})
    
    @app.route('/health')
    def health():
        return jsonify({"status": "healthy", "error": str(e)})
    
    handler = app 