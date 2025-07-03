"""
简单的测试文件，用于验证基本功能
"""
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "message": "简单测试应用正在运行",
        "environment": "vercel",
        "openai_key_set": bool(os.getenv('OPENAI_API_KEY'))
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/debug')
def debug():
    return jsonify({
        "cwd": os.getcwd(),
        "files": os.listdir('.'),
        "environment_vars": {k: v for k, v in os.environ.items() if 'VERCEL' in k or 'OPENAI' in k}
    })

if __name__ == '__main__':
    app.run(debug=True, port=8080) 