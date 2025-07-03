from flask import Flask, render_template, request, jsonify
import os
import sys
import json
from datetime import datetime
import numpy as np
import asyncio
import tiktoken
from lightrag import QueryParam

# 添加 LightRAG 路径
sys.path.append('/Users/blairzhang/Desktop/MyProject/LightRAG-main/LightRAG')

from lightrag import LightRAG
from lightrag.llm import openai_complete_if_cache, openai_embedding
from lightrag.utils import EmbeddingFunc

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
        "input_cost_per_1k_tokens": 0.00015,  # $0.00015 per 1K input tokens
        "output_cost_per_1k_tokens": 0.0006,  # $0.0006 per 1K output tokens
    },
    "text-embedding-ada-002": {
        "cost_per_1k_tokens": 0.0001,  # $0.0001 per 1K tokens
    }
}

# 评分系统配置
SCORING_CONFIG = {
    "comprehensiveness_weight": 0.4,
    "diversity_weight": 0.3,
    "empowerment_weight": 0.3,
    "max_score": 10.0
}

def initialize_rag():
    """初始化 LightRAG"""
    global rag, token_encoder
    
    # 从环境变量获取 API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # 尝试从.env文件读取（本地开发）
        try:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("OPENAI_API_KEY")
        except ImportError:
            pass
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it in your environment or .env file.")
    
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
            api_key=os.getenv("OPENAI_API_KEY"),
            **kwargs
        )

    async def embedding_func(texts: list[str]) -> np.ndarray:
        return await openai_embedding(
            texts,
            model="text-embedding-ada-002",
            api_key=os.getenv("OPENAI_API_KEY")
        )

    # 初始化LightRAG，使用与成功代码相同的配置
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
    
    print("✅ LightRAG 初始化完成")

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
    return len(token_encoder.encode(text))

def calculate_cost(input_tokens, output_tokens, embedding_tokens=0):
    """计算API调用成本"""
    # 计算LLM成本
    llm_input_cost = (input_tokens / 1000) * COST_CONFIG["gpt-4o-mini"]["input_cost_per_1k_tokens"]
    llm_output_cost = (output_tokens / 1000) * COST_CONFIG["gpt-4o-mini"]["output_cost_per_1k_tokens"]
    
    # 计算embedding成本
    embedding_cost = (embedding_tokens / 1000) * COST_CONFIG["text-embedding-ada-002"]["cost_per_1k_tokens"]
    
    total_cost = llm_input_cost + llm_output_cost + embedding_cost
    
    return {
        "llm_input_cost": llm_input_cost,
        "llm_output_cost": llm_output_cost,
        "embedding_cost": embedding_cost,
        "total_cost": total_cost
    }

def score_response(query, response, mode):
    """评分系统：基于原始文件的评估标准"""
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
    query_complexity = len(query.split())
    
    if is_general_question:
        # 对于通用问题，只要不是"Insufficient Data"就给高分
        if "信息不足" not in response and "Insufficient Data" not in response:
            scores["comprehensiveness"] = 8.0
        else:
            # 如果是通用问题但返回了Insufficient Data，给较低分
            scores["comprehensiveness"] = 3.0
    else:
        # 对于项目相关问题，使用原有逻辑
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
    empowerment_keywords = ["建议", "推荐", "考虑", "分析", "评估", "建议", "recommend", "consider", "analyze", "evaluate"]
    empowerment_count = sum(1 for keyword in empowerment_keywords if keyword.lower() in response.lower())
    scores["empowerment"] = min(10.0, empowerment_count * 2)
    
    # 对于通用问题，增加empowerment分数
    if is_general_question and "信息不足" not in response and "Insufficient Data" not in response:
        scores["empowerment"] = min(10.0, scores["empowerment"] + 3.0)
    
    # 根据查询模式调整分数
    mode_bonus = {
        "mix": 1.2,
        "hybrid": 1.1,
        "global": 1.0,
        "local": 0.9,
        "naive": 0.8
    }
    
    for key in scores:
        scores[key] *= mode_bonus.get(mode, 1.0)
        scores[key] = min(10.0, scores[key])
    
    # 计算加权总分
    total_score = (
        scores["comprehensiveness"] * SCORING_CONFIG["comprehensiveness_weight"] +
        scores["diversity"] * SCORING_CONFIG["diversity_weight"] +
        scores["empowerment"] * SCORING_CONFIG["empowerment_weight"]
    )
    
    return {
        "total_score": round(total_score, 2),
        "comprehensiveness_score": scores["comprehensiveness"],
        "diversity_score": scores["diversity"],
        "empowerment_score": scores["empowerment"],
        "feedback": [
            f"Comprehensiveness: {scores['comprehensiveness']:.1f}/10",
            f"Diversity: {scores['diversity']:.1f}/10",
            f"Empowerment: {scores['empowerment']:.1f}/10"
        ]
    }

def query_with_best_mode(question, language):
    """自动选择最佳模式的查询功能"""
    modes = ["naive", "local", "global", "hybrid", "mix"]
    best_result = None
    best_score = 0
    best_mode = "mix"
    mode_results = {}
    
    # 生成系统提示词
    system_prompt = generate_system_prompt(question, language)
    
    # 临时替换 llm_model_func 以传递系统提示
    original_llm_func = rag.llm_model_func
    
    async def llm_with_system_prompt(prompt, system_prompt=None, history_messages=[], **kwargs):
        return await original_llm_func(prompt, system_prompt=system_prompt, history_messages=history_messages, **kwargs)
    
    rag.llm_model_func = llm_with_system_prompt
    
    try:
        # 测试所有模式
        for mode in modes:
            try:
                # 执行查询
                response = rag.query(question, param=QueryParam(mode=mode, top_k=10))
                
                # 计算token和成本
                input_tokens = calculate_tokens(question)
                output_tokens = calculate_tokens(response)
                cost_info = calculate_cost(input_tokens, output_tokens)
                
                # 评分
                score_info = score_response(question, response, mode)
                
                # 记录结果
                result = {
                    "response": response,
                    "mode": mode,
                    "score": score_info["total_score"],
                    "cost": cost_info,
                    "tokens": {
                        "input": input_tokens,
                        "output": output_tokens
                    },
                    "score_details": score_info
                }
                
                mode_results[mode] = result
                
                # 更新最佳结果
                if score_info["total_score"] > best_score:
                    best_score = score_info["total_score"]
                    best_result = result
                    best_mode = mode
                    
            except Exception as e:
                print(f"模式 {mode} 查询失败: {e}")
                continue
        
        # 恢复原始 llm_model_func
        rag.llm_model_func = original_llm_func
        
        if best_result:
            # 更新成本统计 - 只计算最佳模式的成本
            cost_stats["total_input_tokens"] += best_result["tokens"]["input"]
            cost_stats["total_output_tokens"] += best_result["tokens"]["output"]
            cost_stats["total_cost"] += best_result["cost"]["total_cost"]
            
            # 记录查询历史
            query_record = {
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "question": question,
                "response": best_result["response"],
                "mode": best_mode,
                "language": language,
                "score": best_result["score"],
                "cost": best_result["cost"]["total_cost"],
                "input_tokens": best_result["tokens"]["input"],
                "output_tokens": best_result["tokens"]["output"],
                "all_mode_results": mode_results
            }
            query_history.append(query_record)
            
            return {
                "response": best_result["response"],
                "timestamp": query_record["timestamp"],
                "language": language,
                "mode": best_mode,
                "score": best_result["score_details"],
                "cost": best_result["cost"],
                "tokens": best_result["tokens"],
                "mode_results": mode_results,
                "best_mode": best_mode
            }
        else:
            return {"error": "所有模式都查询失败"}
            
    except Exception as e:
        # 恢复原始 llm_model_func
        rag.llm_model_func = original_llm_func
        return {"error": f"查询出错: {str(e)}"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        question = data.get('message', '')
        mode = data.get('mode', 'best')  # 默认使用最佳模式
        
        if not question:
            return jsonify({'error': '请输入问题'})
        
        # 检测语言
        language = detect_language(question)
        
        if mode == 'best':
            # 自动选择最佳模式
            result = query_with_best_mode(question, language)
        else:
            # 使用指定模式
            system_prompt = generate_system_prompt(question, language)
            
            # 临时替换 llm_model_func 以传递系统提示
            original_llm_func = rag.llm_model_func
            
            async def llm_with_system_prompt(prompt, system_prompt=None, history_messages=[], **kwargs):
                return await original_llm_func(prompt, system_prompt=system_prompt, history_messages=history_messages, **kwargs)
            
            rag.llm_model_func = llm_with_system_prompt
            
            try:
                # 使用同步查询方法
                response = rag.query(question, param=QueryParam(mode=mode, top_k=10))
                
                # 计算token和成本
                input_tokens = calculate_tokens(question)
                output_tokens = calculate_tokens(response)
                cost_info = calculate_cost(input_tokens, output_tokens)
                
                # 更新成本统计
                cost_stats["total_input_tokens"] += input_tokens
                cost_stats["total_output_tokens"] += output_tokens
                cost_stats["total_cost"] += cost_info["total_cost"]
                
                # 评分
                score_info = score_response(question, response, mode)
                
                # 记录查询历史
                query_record = {
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "question": question,
                    "response": response,
                    "mode": mode,
                    "language": language,
                    "score": score_info["total_score"],
                    "cost": cost_info["total_cost"],
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }
                query_history.append(query_record)
                
                result = {
                    'response': response,
                    'timestamp': query_record["timestamp"],
                    'language': language,
                    'mode': mode,
                    'score': score_info,
                    'cost': cost_info,
                    'tokens': {
                        'input': input_tokens,
                        'output': output_tokens
                    }
                }
            finally:
                # 恢复原始 llm_model_func
                rag.llm_model_func = original_llm_func
        
        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']})
        else:
            return jsonify({
                'success': True,
                'response': result['response'],
                'timestamp': result.get('timestamp', ''),
                'language': result.get('language', 'english'),
                'mode_used': result.get('mode', result.get('best_mode', 'unknown')),
                'processing_time': 0,  # 可以后续添加实际处理时间
                'score': result.get('score', {}),
                'cost': result.get('cost', {}),
                'tokens': result.get('tokens', {})
            })
        
    except Exception as e:
        return jsonify({'error': f'错误：{str(e)}'})

@app.route('/stats')
def get_stats():
    """获取统计信息"""
    return jsonify({
        'cost_stats': cost_stats,
        'query_history': query_history[-10:],  # 最近10条记录
        'total_queries': len(query_history)
    })

@app.route('/test_modes')
def test_modes():
    """测试不同查询模式"""
    test_question = "What are the key stakeholder engagement strategies in the Scarborough project?"
    modes = ["naive", "local", "global", "hybrid", "mix"]
    results = []
    
    for mode in modes:
        try:
            response = rag.query(test_question, param=QueryParam(mode=mode, top_k=10))
            score_info = score_response(test_question, response, mode)
            results.append({
                'mode': mode,
                'response': response[:200] + "..." if len(response) > 200 else response,
                'score': score_info["total_score"],
                'feedback': score_info["feedback"]
            })
        except Exception as e:
            results.append({
                'mode': mode,
                'error': str(e)
            })
    
    return jsonify({'test_results': results})

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'rag_initialized': rag is not None,
        'total_queries': len(query_history),
        'total_cost': cost_stats["total_cost"]
    })

if __name__ == '__main__':
    print("🚀 初始化 Stakeholder Management Chatbot Web 界面...")
    initialize_rag()
    print("🌐 启动 Web 服务器...")
    app.run(host='0.0.0.0', port=8081, debug=True) 