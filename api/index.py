"""
Vercel Serverless Function - 简化版聊天机器人API
使用OpenAI直接调用，不依赖LightRAG
"""
import os
import sys
import json
from datetime import datetime
import tiktoken
from flask import Flask, render_template, request, jsonify
import openai

app = Flask(__name__)

# 全局变量
token_encoder = None
cost_stats = {
    "total_input_tokens": 0,
    "total_output_tokens": 0,
    "total_embedding_tokens": 0,
    "total_cost": 0.0
}
query_history = []

# 成本估算配置
COST_CONFIG = {
    "gpt-4o-mini": {
        "input_cost_per_1k_tokens": 0.00015,
        "output_cost_per_1k_tokens": 0.0006,
    },
    "text-embedding-ada-002": {
        "cost_per_1k_tokens": 0.0001,
    }
}

def initialize_openai():
    """初始化OpenAI客户端"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    
    openai.api_key = api_key
    return openai

def initialize_tokenizer():
    """初始化token编码器"""
    global token_encoder
    try:
        token_encoder = tiktoken.encoding_for_model("gpt-4o-mini")
    except Exception as e:
        print(f"⚠️ Token编码器初始化失败: {e}")
        token_encoder = None

def detect_language(text):
    """简单的中英文检测"""
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    return 'chinese' if chinese_chars > len(text) * 0.3 else 'english'

def generate_system_prompt(question, language='english'):
    """生成智能系统提示词"""
    if language == 'chinese':
        return f"""你是一个专业的利益相关者管理顾问。请基于你的专业知识回答用户问题。

回答要求：
1. 提供专业、准确的建议
2. 使用结构化的回答格式，包含要点和子要点
3. 如果信息不足，请诚实说明
4. 保持专业、客观的语气
5. 提供实用的建议和指导

用户问题：{question}

请基于以上要求回答："""
    else:
        return f"""You are a professional stakeholder management consultant. Please answer user questions based on your expertise.

Answer requirements:
1. Provide professional and accurate advice
2. Use structured answer format with bullet points and sub-points
3. If information is insufficient, state honestly
4. Maintain professional and objective tone
5. Provide practical recommendations and guidance

User question: {question}

Please answer based on the above requirements:"""

def calculate_tokens(text):
    """计算文本的token数量"""
    if token_encoder:
        return len(token_encoder.encode(text))
    return len(text.split())  # 简单估算

def calculate_cost(input_tokens, output_tokens, embedding_tokens=0):
    """计算API调用成本"""
    llm_input_cost = (input_tokens / 1000) * COST_CONFIG["gpt-4o-mini"]["input_cost_per_1k_tokens"]
    llm_output_cost = (output_tokens / 1000) * COST_CONFIG["gpt-4o-mini"]["output_cost_per_1k_tokens"]
    embedding_cost = (embedding_tokens / 1000) * COST_CONFIG["text-embedding-ada-002"]["cost_per_1k_tokens"]
    
    total_cost = llm_input_cost + llm_output_cost + embedding_cost
    
    return {
        "llm_input_cost": llm_input_cost,
        "llm_output_cost": llm_output_cost,
        "embedding_cost": embedding_cost,
        "total_cost": total_cost
    }

def score_response(query, response, mode):
    """评分系统"""
    scores = {
        "comprehensiveness": 0.0,
        "diversity": 0.0,
        "empowerment": 0.0
    }
    
    # 检测通用问题类型
    general_questions = [
        "hi", "hello", "hey", "你好", "您好",
        "who are you", "what are you", "你是谁", "你是什么",
        "how are you", "你好吗", "你好吗？",
        "thanks", "thank you", "谢谢", "谢谢您",
        "bye", "goodbye", "再见", "拜拜"
    ]
    
    query_lower = query.lower().strip()
    is_general_question = any(gq in query_lower for gq in general_questions)
    
    # 计算comprehensiveness（完整性）
    response_length = len(response)
    
    if is_general_question:
        if "信息不足" not in response and "Insufficient Data" not in response:
            scores["comprehensiveness"] = 8.0
        else:
            scores["comprehensiveness"] = 3.0
    else:
        if response_length > 100 and "信息不足" not in response and "Insufficient Data" not in response:
            scores["comprehensiveness"] = min(10.0, response_length / 50)
        else:
            scores["comprehensiveness"] = max(1.0, response_length / 20)
    
    # 计算diversity（多样性）
    unique_words = len(set(response.lower().split()))
    total_words = len(response.split())
    if total_words > 0:
        diversity_ratio = unique_words / total_words
        scores["diversity"] = min(10.0, diversity_ratio * 15)
    
    # 计算empowerment（启发性）
    empowerment_keywords = ["建议", "推荐", "考虑", "分析", "评估", "建议", "推荐", "考虑", "分析", "评估"]
    empowerment_count = sum(1 for keyword in empowerment_keywords 
                           if keyword.lower() in response.lower())
    scores["empowerment"] = min(10.0, empowerment_count * 2)
    
    # 计算总分
    total_score = (
        scores["comprehensiveness"] * 0.4 +
        scores["diversity"] * 0.3 +
        scores["empowerment"] * 0.3
    )
    
    scores["total_score"] = round(total_score, 1)
    
    # 生成反馈
    feedback = []
    if scores["comprehensiveness"] >= 7:
        feedback.append("✅ 回答完整详细")
    elif scores["comprehensiveness"] >= 4:
        feedback.append("⚠️ 回答较为完整")
    else:
        feedback.append("❌ 回答不够详细")
    
    if scores["diversity"] >= 7:
        feedback.append("✅ 词汇丰富多样")
    elif scores["diversity"] >= 4:
        feedback.append("⚠️ 词汇较为多样")
    else:
        feedback.append("❌ 词汇较为单一")
    
    if scores["empowerment"] >= 7:
        feedback.append("✅ 具有指导性")
    elif scores["empowerment"] >= 4:
        feedback.append("⚠️ 具有一定指导性")
    else:
        feedback.append("❌ 缺乏指导性")
    
    scores["feedback"] = feedback
    
    return scores

def query_openai(question, language):
    """使用OpenAI API查询"""
    try:
        # 初始化OpenAI
        client = initialize_openai()
        
        # 生成系统提示词
        system_prompt = generate_system_prompt(question, language)
        
        # 调用OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"抱歉，查询失败: {str(e)}"

# 初始化
try:
    initialize_tokenizer()
    print("✅ Token编码器初始化完成")
except Exception as e:
    print(f"❌ Token编码器初始化失败: {e}")

# 路由定义
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/index.html')
def index_html():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """聊天接口"""
    try:
        data = request.get_json()
        question = data.get('message', '')
        mode = data.get('mode', 'best')
        
        if not question.strip():
            return jsonify({'success': False, 'error': '问题不能为空'})
        
        # 检测语言
        language = detect_language(question)
        
        # 查询处理
        response = query_openai(question, language)
        
        # 计算token和成本
        input_tokens = calculate_tokens(question)
        output_tokens = calculate_tokens(response)
        cost_info = calculate_cost(input_tokens, output_tokens)
        
        # 评分
        score_info = score_response(question, response, mode)
        
        # 更新统计
        cost_stats["total_input_tokens"] += input_tokens
        cost_stats["total_output_tokens"] += output_tokens
        cost_stats["total_cost"] += cost_info["total_cost"]
        
        # 添加到历史记录
        query_history.append({
            "question": question,
            "response": response,
            "mode": mode,
            "timestamp": datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'response': response,
            'mode_used': mode,
            'score': score_info,
            'cost': cost_info,
            'tokens': {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stats')
def get_stats():
    """统计信息接口"""
    return jsonify({
        'cost_stats': cost_stats,
        'query_history': query_history[-10:],
        'total_queries': len(query_history)
    })

@app.route('/health')
def health():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'api_key_set': bool(os.getenv("OPENAI_API_KEY")),
        'environment': os.getenv("VERCEL_ENV", "unknown"),
        'version': 'simplified-1.0'
    })

@app.route('/test')
def test():
    """测试接口"""
    return jsonify({
        'message': 'API服务器正常运行',
        'timestamp': datetime.now().isoformat(),
        'version': 'simplified-1.0',
        'mode': 'openai_direct'
    })

# Vercel Serverless Function Handler
def handler(request, context):
    """Vercel无服务器函数入口点"""
    return app(request, context) 