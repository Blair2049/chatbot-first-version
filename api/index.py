"""
Vercel部署入口文件
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入Flask应用
from chatbot_web import app

# 设置生产环境
app.debug = False 