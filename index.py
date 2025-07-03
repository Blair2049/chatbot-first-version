"""
备用Vercel入口文件
"""
import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入Flask应用
from chatbot_web import app

# 设置生产环境
app.debug = False

# Vercel需要这个变量来识别Flask应用
handler = app 