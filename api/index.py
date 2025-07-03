"""
Vercel部署入口文件
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print(f"🔍 当前工作目录: {os.getcwd()}")
print(f"🔍 项目根目录: {project_root}")
print(f"🔍 Python路径: {sys.path[:3]}")

# 检查环境变量
print(f"🔍 OPENAI_API_KEY 是否存在: {bool(os.getenv('OPENAI_API_KEY'))}")
print(f"🔍 VERCEL环境: {os.getenv('VERCEL')}")

try:
    # 导入Flask应用
    print("🔄 正在导入Flask应用...")
    from chatbot_web import app
    
    # 设置生产环境
    app.debug = False
    
    # Vercel需要这个变量来识别Flask应用
    handler = app
    
    print("✅ Flask应用成功导入")
    
except Exception as e:
    print(f"❌ 导入Flask应用失败: {e}")
    import traceback
    traceback.print_exc()
    
    # 创建一个简单的测试应用
    from flask import Flask, jsonify
    
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return jsonify({
            "message": "Flask应用正在运行", 
            "error": str(e),
            "environment": "vercel",
            "python_path": str(sys.path[:3])
        })
    
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy", 
            "error": str(e),
            "openai_key_set": bool(os.getenv('OPENAI_API_KEY'))
        })
    
    @app.route('/debug')
    def debug():
        return jsonify({
            "cwd": os.getcwd(),
            "files": os.listdir('.'),
            "python_version": sys.version,
            "environment_vars": {k: v for k, v in os.environ.items() if 'VERCEL' in k or 'OPENAI' in k}
        })
    
    handler = app 