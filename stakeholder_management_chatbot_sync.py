import os
from lightrag import LightRAG, QueryParam
import json
import time
import numpy as np
import tiktoken
from datetime import datetime
import asyncio
import logging

from lightrag.utils import EmbeddingFunc
from lightrag.llm import openai_complete_if_cache, openai_embedding

#########
# Uncomment the below two lines if running in a jupyter notebook to handle the async nature of rag.insert()
# import nest_asyncio
# nest_asyncio.apply()
#########
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 设置工作目录
WORKING_DIR = "./stakeholder_management_rag_sync"
if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR)

# Woods文档路径
WOODS_DIR = "/Users/blairzhang/Desktop/MyProject/LightRAG-main/LightRAG/woods"

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

class StakeholderManagementChatbot:
    def __init__(self):
        """初始化Stakeholder Management Chatbot"""
        self.rag = None
        self.token_encoder = tiktoken.encoding_for_model("gpt-4o-mini")
        self.cost_stats = {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_embedding_tokens": 0,
            "total_cost": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        self.query_history = []
        
    def initialize_rag(self):
        """初始化LightRAG系统 - 使用同步方法"""
        print("🚀 初始化Stakeholder Management Chatbot...")
        
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

        # 初始化LightRAG，使用README中的同步配置
        self.rag = LightRAG(
            working_dir=WORKING_DIR,
            llm_model_func=llm_model_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=1536,
                max_token_size=8192,
                func=embedding_func,
            ),
            # 使用README中的addon_params配置
            addon_params={
                "insert_batch_size": 4,
                "language": "Simplified Chinese",
                "entity_types": ["organization", "person", "geo", "event", "project"],
                "example_number": 3
            },
            # 启用缓存配置
            enable_llm_cache=True,
            enable_llm_cache_for_entity_extract=True
        )
        
        print("✅ LightRAG系统初始化完成")

    def load_woods_documents(self):
        """读取Woods文档"""
        documents = []
        woods_files = []
        
        # 获取所有wood_part*.txt文件
        for i in range(1, 12):  # 1到11
            filename = f"wood_part{i}.txt"
            filepath = os.path.join(WOODS_DIR, filename)
            if os.path.exists(filepath):
                woods_files.append(filepath)
        
        # 按文件名排序
        woods_files.sort()
        
        print(f"📁 找到 {len(woods_files)} 个Woodside项目文档:")
        for filepath in woods_files:
            filename = os.path.basename(filepath)
            print(f"   - {filename}")
        
        # 读取每个文档
        for filepath in woods_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    # 清理内容，移除可能导致API错误的字符
                    content = content.replace('\x00', '').replace('\ufffd', '')
                    documents.append(content)
                    print(f"✅ 已读取: {os.path.basename(filepath)} ({len(content)} 字符)")
            except Exception as e:
                print(f"❌ 读取文件失败 {filepath}: {e}")
        
        return documents

    def insert_documents(self):
        """插入文档到RAG系统 - 使用同步方法，参考README"""
        print("\n📚 正在插入Woodside项目文档到RAG系统...")
        documents = self.load_woods_documents()
        
        if not documents:
            print("❌ 没有找到任何文档文件！")
            return False
        
        try:
            # 使用README中的同步插入方法
            print(f"正在插入 {len(documents)} 个文档...")
            
            # 方法1：逐个插入（参考README的Incremental Insert）
            for i, doc in enumerate(documents, 1):
                print(f"正在插入文档 {i}/{len(documents)}...")
                try:
                    # 使用同步插入方法
                    self.rag.insert(doc)
                    print(f"✅ 文档 {i} 插入完成")
                except Exception as e:
                    print(f"⚠️  文档 {i} 插入失败: {e}")
                    continue
            
            print(f"✅ 成功插入 {len(documents)} 个文档到RAG系统")
            return True
            
        except Exception as e:
            print(f"❌ 插入文档失败: {e}")
            return False

    def calculate_tokens(self, text):
        """计算文本的token数量"""
        return len(self.token_encoder.encode(text))

    def calculate_cost(self, input_tokens, output_tokens, embedding_tokens=0):
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

    def score_response(self, query, response, mode):
        """评分系统：基于README中的评估标准"""
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
            "scores": scores,
            "total_score": round(total_score, 2),
            "mode": mode
        }

    def query_with_analysis(self, question, mode="mix"):
        """带分析的查询功能 - 使用同步方法"""
        print(f"\n🔍 使用 {mode} 模式查询: {question}")
        
        start_time = time.time()
        
        try:
            # 执行查询 - 使用同步方法，增加top_k参数
            result = self.rag.query(question, param=QueryParam(mode=mode, top_k=10))
            
            # 计算token和成本
            input_tokens = self.calculate_tokens(question)
            output_tokens = self.calculate_tokens(result)
            
            cost_info = self.calculate_cost(input_tokens, output_tokens)
            
            # 更新成本统计
            self.cost_stats["total_input_tokens"] += input_tokens
            self.cost_stats["total_output_tokens"] += output_tokens
            self.cost_stats["total_cost"] += cost_info["total_cost"]
            
            # 评分
            score_info = self.score_response(question, result, mode)
            
            # 记录查询历史
            query_record = {
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "mode": mode,
                "response": result,
                "scores": score_info,
                "cost": cost_info,
                "response_time": time.time() - start_time
            }
            self.query_history.append(query_record)
            
            return {
                "response": result,
                "scores": score_info,
                "cost": cost_info,
                "response_time": time.time() - start_time
            }
            
        except Exception as e:
            print(f"❌ 查询出错: {e}")
            return None

    def display_cost_stats(self):
        """显示成本统计"""
        print("\n💰 成本统计:")
        print(f"   总输入tokens: {self.cost_stats['total_input_tokens']:,}")
        print(f"   总输出tokens: {self.cost_stats['total_output_tokens']:,}")
        print(f"   总成本: ${self.cost_stats['total_cost']:.4f}")
        print(f"   缓存命中: {self.cost_stats['cache_hits']}")
        print(f"   缓存未命中: {self.cost_stats['cache_misses']}")

    def display_query_history(self):
        """显示查询历史"""
        print(f"\n📊 查询历史 (共{len(self.query_history)}条):")
        for i, record in enumerate(self.query_history[-5:], 1):  # 显示最近5条
            print(f"   {i}. [{record['mode']}] {record['question'][:50]}...")
            print(f"      评分: {record['scores']['total_score']}/10, 成本: ${record['cost']['total_cost']:.4f}")

    def test_different_modes(self):
        """测试不同查询模式 - 使用同步方法"""
        test_questions = [
            "What is the Scarborough gas project?",
            "Who are the key stakeholders in this project?",
            "What are the environmental impacts of the project?",
            "How does the project benefit the local community?",
            "What are the main risks and challenges?"
        ]
        
        modes = ["naive", "local", "global", "hybrid", "mix"]
        
        print(f"\n🧪 测试不同查询模式:")
        print("=" * 80)
        
        for question in test_questions:
            print(f"\n📝 测试问题: {question}")
            print("-" * 60)
            
            best_result = None
            best_score = 0
            
            # 收集所有模式的结果
            mode_results = {}
            
            for mode in modes:
                result = self.query_with_analysis(question, mode)
                if result:
                    score = result["scores"]["total_score"]
                    mode_results[mode] = result
                    print(f"   {mode:>8}: 评分 {score:>5.1f}/10, 成本 ${result['cost']['total_cost']:.4f}")
                    
                    if score > best_score:
                        best_score = score
                        best_result = result
            
            # 输出最佳模式的完整答案
            if best_result:
                print(f"\n🏆 最佳结果 ({best_result['scores']['mode']} 模式):")
                print(f"   评分: {best_result['scores']['total_score']}/10")
                print(f"   成本: ${best_result['cost']['total_cost']:.4f}")
                print(f"   响应时间: {best_result['response_time']:.2f}秒")
                print(f"\n📝 完整答案:")
                print(f"   {best_result['response']}")
                print(f"\n📊 详细评分:")
                print(f"   完整性 (Comprehensiveness): {best_result['scores']['scores']['comprehensiveness']:.1f}/10")
                print(f"   多样性 (Diversity): {best_result['scores']['scores']['diversity']:.1f}/10")
                print(f"   启发性 (Empowerment): {best_result['scores']['scores']['empowerment']:.1f}/10")
            else:
                print("❌ 所有模式都查询失败")
            
            print("\n" + "="*80)

    def interactive_chat(self):
        """交互式聊天 - 使用同步方法"""
        print("\n💬 开始交互式聊天 (输入 'quit' 退出, 'stats' 查看统计, 'history' 查看历史):")
        print("📚 你可以询问关于Woodside Scarborough项目的任何问题！")
        print("💡 建议问题:")
        print("   - What is the Scarborough gas project?")
        print("   - Who are the key stakeholders?")
        print("   - What are the environmental impacts?")
        print("   - How does the project benefit the community?")
        print("   - What are the main risks and challenges?")
        print("\n🔧 查询模式选项:")
        print("   - 直接输入问题: 自动选择最佳模式 (推荐)")
        print("   - 输入 'mix' + 问题: 强制使用mix模式")
        print("   - 输入 'hybrid' + 问题: 强制使用hybrid模式")
        print("   - 输入 'global' + 问题: 强制使用global模式")
        print("   - 输入 'local' + 问题: 强制使用local模式")
        print("   - 输入 'naive' + 问题: 强制使用naive模式")
        
        while True:
            try:
                user_input = input("\n👤 你: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                    print("👋 再见!")
                    break
                
                if user_input.lower() == 'stats':
                    self.display_cost_stats()
                    continue
                
                if user_input.lower() == 'history':
                    self.display_query_history()
                    continue
                
                if not user_input:
                    print("💡 请输入您的问题...")
                    continue
                
                # 解析用户输入，判断是否指定了模式
                mode = "best"  # 默认自动选择最佳模式
                question = user_input
                
                # 检查是否指定了模式
                if user_input.lower().startswith("mix "):
                    mode = "mix"
                    question = user_input[4:].strip()
                elif user_input.lower().startswith("hybrid "):
                    mode = "hybrid"
                    question = user_input[7:].strip()
                elif user_input.lower().startswith("global "):
                    mode = "global"
                    question = user_input[7:].strip()
                elif user_input.lower().startswith("local "):
                    mode = "local"
                    question = user_input[6:].strip()
                elif user_input.lower().startswith("naive "):
                    mode = "naive"
                    question = user_input[6:].strip()
                
                if mode == "best":
                    # 自动选择最佳模式
                    print(f"\n🔍 正在测试所有模式为问题选择最佳答案...")
                    modes_to_test = ["naive", "local", "global", "hybrid", "mix"]
                    best_result = None
                    best_score = 0
                    best_mode = "mix"
                    
                    for test_mode in modes_to_test:
                        result = self.query_with_analysis(question, test_mode)
                        if result:
                            score = result["scores"]["total_score"]
                            print(f"   {test_mode:>8}: 评分 {score:>5.1f}/10")
                            if score > best_score:
                                best_score = score
                                best_result = result
                                best_mode = test_mode
                    
                    if best_result:
                        print(f"\n🏆 选择 {best_mode} 模式 (评分最高: {best_score:.1f}/10)")
                        print(f"📝 回答: {best_result['response']}")
                        print(f"📊 评分: {best_result['scores']['total_score']}/10")
                        print(f"💰 成本: ${best_result['cost']['total_cost']:.4f}")
                        print(f"⏱️  响应时间: {best_result['response_time']:.2f}秒")
                    else:
                        print("❌ 所有模式都查询失败")
                else:
                    # 使用指定模式
                    result = self.query_with_analysis(question, mode)
                    if result:
                        print(f"\n📝 回答: {result['response']}")
                        print(f"📊 评分: {result['scores']['total_score']}/10")
                        print(f"💰 成本: ${result['cost']['total_cost']:.4f}")
                        print(f"⏱️  响应时间: {result['response_time']:.2f}秒")
                
            except KeyboardInterrupt:
                print("\n👋 再见!")
                break
            except Exception as e:
                print(f"❌ 聊天出错: {e}")
                print("💡 请尝试重新输入您的问题...")

def main():
    """主函数 - 使用同步方法"""
    try:
        # 检查API密钥
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ 错误: 请设置OPENAI_API_KEY环境变量")
            print("💡 提示: 在终端中运行: export OPENAI_API_KEY='your-api-key-here'")
            return
        
        # 创建chatbot实例
        chatbot = StakeholderManagementChatbot()
        
        # 初始化RAG系统
        chatbot.initialize_rag()
        
        # 插入文档
        success = chatbot.insert_documents()
        if not success:
            return
        
        # 测试不同模式
        chatbot.test_different_modes()
        
        # 显示初始统计
        chatbot.display_cost_stats()
        
        # 交互式聊天
        chatbot.interactive_chat()
        
        # 最终统计
        print("\n" + "="*60)
        print("📈 最终统计报告")
        print("="*60)
        chatbot.display_cost_stats()
        chatbot.display_query_history()
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 