#!/bin/bash

echo "🔧 LightRAG Chatbot 环境设置"
echo "================================"

# 检查是否已设置API密钥
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ 未检测到 OPENAI_API_KEY 环境变量"
    echo ""
    echo "请按以下步骤设置："
    echo "1. 获取你的 OpenAI API 密钥"
    echo "2. 运行以下命令："
    echo "   export OPENAI_API_KEY='your-api-key-here'"
    echo ""
    echo "或者创建 .env 文件："
    echo "echo 'OPENAI_API_KEY=your-api-key-here' > .env"
    echo ""
    echo "💡 提示：你可以从 https://platform.openai.com/api-keys 获取API密钥"
else
    echo "✅ OPENAI_API_KEY 已设置"
fi

echo ""
echo "📦 安装依赖包..."
pip install -r requirements.txt

echo ""
echo "🚀 现在可以运行以下命令："
echo "python simple_test.py    # 快速测试"
echo "python lightrag_chatbot.py    # 完整功能"
echo "python fixed_original.py    # 修复版原始代码" 