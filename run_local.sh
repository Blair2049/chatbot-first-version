#!/bin/bash

# 本地开发运行脚本

echo "🚀 启动 Stakeholder Management Chatbot (本地开发模式)"

# 检查是否存在.env文件
if [ ! -f .env ]; then
    echo "⚠️  未找到.env文件，请创建.env文件并设置OPENAI_API_KEY"
    echo "📝 示例："
    echo "OPENAI_API_KEY=your_api_key_here"
    echo "FLASK_ENV=development"
    echo "FLASK_DEBUG=true"
    exit 1
fi

# 加载环境变量
export $(cat .env | xargs)

# 检查API密钥
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY 未设置"
    exit 1
fi

echo "✅ 环境变量加载成功"
echo "🌐 启动Web服务..."

# 启动Flask应用
python chatbot_web.py 