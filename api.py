"""
Vercel适配文件 - 无服务器函数入口
"""
import os
import sys
from flask import Flask, render_template, request, jsonify
import numpy as np
import asyncio
import tiktoken
from lightrag import QueryParam

# 添加 LightRAG 路径
sys.path.append('/Users/blairzhang/Desktop/MyProject/LightRAG-main/LightRAG')

from lightrag import LightRAG
from lightrag.llm import openai_complete_if_cache, openai_embedding
from lightrag.utils import EmbeddingFunc

# 创建Flask应用
app = Flask(__name__)

# 全局变量
rag = None
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

def initialize_rag():
    """初始化 LightRAG"""
    global rag, token_encoder
    
    # 从环境变量获取 API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    
    # 初始化 token 编码器
    token_encoder = tiktoken.encoding_for_model("gpt-4o-mini")
    
    # 定义LLM和embedding函数
    async def llm_model_func(
        prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
    ) -> str:
        return await openai_complete_if_cache(
            "gpt-4o-mini",
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            api_key=api_key,
            **kwargs
        )

    async def embedding_func(texts: list[str]) -> np.ndarray:
        return await openai_embedding(
            texts,
            model="text-embedding-ada-002",
            api_key=api_key
        )

    # 初始化LightRAG
    rag = LightRAG(
        working_dir="./stakeholder_management_rag_sync",
        llm_model_func=llm_model_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=1536,
            max_token_size=8192,
            func=embedding_func,
        ),
        addon_params={
            "insert_batch_size": 4,
            "language": "Simplified Chinese",
            "entity_types": ["organization", "person", "geo", "event", "project"],
            "example_number": 3
        },
        enable_llm_cache=True,
        enable_llm_cache_for_entity_extract=True
    )

# 初始化RAG（在模块加载时执行）
try:
    initialize_rag()
    print("✅ LightRAG 初始化完成")
except Exception as e:
    print(f"❌ LightRAG 初始化失败: {e}")

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
        chinese_chars = sum(1 for char in question if '\u4e00' <= char <= '\u9fff')
        language = 'chinese' if chinese_chars > len(question) * 0.3 else 'english'
        
        # 生成系统提示词
        system_prompt = generate_system_prompt(question, language)
        
        # 查询处理
        if mode == 'best':
            result = query_with_best_mode(question, language)
        else:
            result = single_mode_query(question, mode, language)
        
        return jsonify({
            'success': True,
            'response': result['response'],
            'mode_used': result.get('mode', 'unknown'),
            'score': result.get('score', {}),
            'cost': result.get('cost', {}),
            'tokens': result.get('tokens', {})
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
    return jsonify({'status': 'healthy', 'rag_initialized': rag is not None})

# 辅助函数（从chatbot_web.py复制）
def detect_language(text):
    """简单的中英文检测"""
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    return 'chinese' if chinese_chars > len(text) * 0.3 else 'english'

def generate_system_prompt(question, language='english'):
    """生成智能系统提示词"""
    if language == 'chinese':
        return f"""你是一个专业的利益相关者管理顾问。基于提供的文档信息，请诚实、准确地回答用户问题。

回答要求：
1. 只基于文档中的信息回答，如果信息不足，请明确说明
2. 提供结构化的回答，使用要点和子要点
3. 如果涉及数据或事实，请引用具体来源
4. 对于评估类问题，如果文档中没有足够的主观评价信息，请说明信息不足
5. 保持专业、客观的语气

用户问题：{question}

请基于以上要求回答："""
    else:
        return f"""You are a professional stakeholder management consultant. Based on the provided document information, please answer user questions honestly and accurately.

Answer requirements:
1. Only answer based on information in the documents, if information is insufficient, clearly state this
2. Provide structured answers using bullet points and sub-points
3. If involving data or facts, cite specific sources
4. For evaluation questions, if documents lack sufficient subjective evaluation information, state insufficient information
5. Maintain professional and objective tone

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

def query_with_best_mode(question, language):
    """自动选择最佳模式的查询功能"""
    if not rag:
        return {"response": "系统初始化失败，请稍后重试", "mode": "error"}
    
    modes = ["naive", "local", "global", "hybrid", "mix"]
    best_result = None
    best_score = 0
    
    for mode in modes:
        try:
            response = rag.query(question, param=QueryParam(mode=mode, top_k=10))
            score_info = score_response(question, response, mode)
            
            if score_info["total_score"] > best_score:
                best_score = score_info["total_score"]
                best_result = {
                    "response": response,
                    "mode": mode,
                    "score": score_info
                }
        except Exception as e:
            print(f"Mode {mode} failed: {e}")
            continue
    
    if not best_result:
        best_result = {
            "response": "抱歉，所有查询模式都失败了，请稍后重试",
            "mode": "error"
        }
    
    return best_result

def single_mode_query(question, mode, language):
    """单一模式查询"""
    if not rag:
        return {"response": "系统初始化失败，请稍后重试", "mode": "error"}
    
    try:
        response = rag.query(question, param=QueryParam(mode=mode, top_k=10))
        score_info = score_response(question, response, mode)
        
        return {
            "response": response,
            "mode": mode,
            "score": score_info
        }
    except Exception as e:
        return {
            "response": f"查询失败: {str(e)}",
            "mode": mode
        }

# Vercel无服务器函数入口
def handler(request, context):
    """Vercel无服务器函数入口点"""
    return app(request, context) 