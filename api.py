"""
Vercel适配文件 - 保持原有chatbot功能不变
"""
import os
import sys
from chatbot_web import app

# 设置环境变量（Vercel会自动从控制台读取）
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8081))) 