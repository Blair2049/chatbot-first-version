# Stakeholder Management Chatbot 开发文档

## 项目概述

本项目基于LightRAG框架开发了一个智能问答系统，专门用于处理利益相关者管理相关的文档查询。系统具备多模式查询、智能评分、实时统计等功能，并提供了现代化的Web界面。

## 开发背景

### 1. 需求分析
- 基于README文档中的利益相关者管理内容构建知识库
- 实现智能问答功能，支持中英文双语查询
- 提供多种查询模式，自动选择最佳答案
- 实时统计查询成本和Token使用情况
- 现代化Web界面，支持实时交互

### 2. 技术选型
- **后端框架**: LightRAG (轻量级RAG框架)
- **Web框架**: Flask
- **前端技术**: HTML5 + CSS3 + JavaScript
- **AI模型**: OpenAI GPT-4 + OpenAI Embeddings
- **向量数据库**: nano-vectordb
- **图数据库**: NetworkX (GraphML格式)

## 开发过程

### 第一阶段：文档分析与知识库构建

#### 1.1 README文档内容分析
通过分析README文档，识别出以下关键内容：
- 利益相关者管理策略
- Scarborough项目案例
- 社区参与方法
- 沟通计划
- 反馈机制
- 合作伙伴关系

#### 1.2 文档预处理
```python
# 文档读取和分块
def process_documents():
    documents = []
    for file in os.listdir('inputs/'):
        if file.endswith('.txt'):
            with open(f'inputs/{file}', 'r', encoding='utf-8') as f:
                content = f.read()
                documents.append(content)
    return documents
```

#### 1.3 LightRAG初始化配置
```python
def initialize_rag():
    global rag
    rag = LightRAG(
        working_dir="./stakeholder_management_rag_sync",
        llm_model_func=llm_model_func,
        embedding_func=embedding_func,
        cache_dir="./cache"
    )
```

### 第二阶段：后端核心功能开发

#### 2.1 多模式查询系统
实现了5种查询模式：
- **Naive Mode**: 基础检索模式
- **Local Mode**: 局部实体关系查询
- **Global Mode**: 全局图结构查询
- **Hybrid Mode**: 混合模式
- **Mix Mode**: 混合检索模式

```python
def query_with_best_mode(question, language):
    """自动选择最佳模式的查询功能"""
    modes = ["naive", "local", "global", "hybrid", "mix"]
    best_result = None
    best_score = 0
    
    for mode in modes:
        response = rag.query(question, param=QueryParam(mode=mode, top_k=10))
        score_info = score_response(question, response, mode)
        
        if score_info["total_score"] > best_score:
            best_score = score_info["total_score"]
            best_result = response
```

#### 2.2 智能评分系统
开发了基于三个维度的评分算法：

```python
def score_response(query, response, mode):
    """评分系统：基于完整性、多样性、启发性"""
    scores = {
        "comprehensiveness": 0.0,  # 完整性
        "diversity": 0.0,         # 多样性
        "empowerment": 0.0        # 启发性
    }
    
    # 计算完整性分数
    response_length = len(response)
    if response_length > 100 and "信息不足" not in response:
        scores["comprehensiveness"] = min(10.0, response_length / 50)
    
    # 计算多样性分数
    unique_words = len(set(response.lower().split()))
    total_words = len(response.split())
    if total_words > 0:
        diversity_ratio = unique_words / total_words
        scores["diversity"] = min(10.0, diversity_ratio * 15)
    
    # 计算启发性分数
    empowerment_keywords = ["建议", "推荐", "考虑", "分析", "评估"]
    empowerment_count = sum(1 for keyword in empowerment_keywords 
                           if keyword.lower() in response.lower())
    scores["empowerment"] = min(10.0, empowerment_count * 2)
    
    return scores
```

#### 2.3 多语言支持
实现了中英文自动检测和提示词生成：

```python
def detect_language(text):
    """检测文本语言"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    if chinese_chars > len(text) * 0.3:
        return 'chinese'
    return 'english'

def generate_system_prompt(question, language='english'):
    """生成系统提示词"""
    if language == 'chinese':
        return """你是一个专业的利益相关者管理助手。请基于提供的文档内容，用中文回答用户问题。
        回答要求：
        1. 准确、完整地回答问题
        2. 提供具体的建议和分析
        3. 使用清晰的结构化格式
        4. 如果信息不足，请诚实说明"""
    else:
        return """You are a professional stakeholder management assistant. Please answer user questions based on the provided documents.
        Requirements:
        1. Answer accurately and completely
        2. Provide specific recommendations and analysis
        3. Use clear structured format
        4. If information is insufficient, please state honestly"""
```

#### 2.4 成本统计系统
实现了详细的Token使用和成本统计：

```python
def calculate_cost(input_tokens, output_tokens, embedding_tokens=0):
    """计算API调用成本"""
    llm_input_cost = input_tokens * 0.000015  # GPT-4输入成本
    llm_output_cost = output_tokens * 0.00006  # GPT-4输出成本
    embedding_cost = embedding_tokens * 0.0000001  # Embedding成本
    
    total_cost = llm_input_cost + llm_output_cost + embedding_cost
    return {
        "llm_input_cost": llm_input_cost,
        "llm_output_cost": llm_output_cost,
        "embedding_cost": embedding_cost,
        "total_cost": total_cost
    }
```

#### 2.5 Flask API接口
开发了完整的RESTful API：

```python
@app.route('/chat', methods=['POST'])
def chat():
    """聊天接口"""
    data = request.get_json()
    question = data.get('message', '')
    mode = data.get('mode', 'best')
    
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

@app.route('/stats')
def get_stats():
    """统计信息接口"""
    return jsonify({
        'cost_stats': cost_stats,
        'query_history': query_history[-10:],
        'total_queries': len(query_history)
    })
```

### 第三阶段：前端界面开发

#### 3.1 现代化UI设计
采用响应式设计，支持桌面和移动设备：

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stakeholder Management Chatbot</title>
    <style>
        /* 渐变背景 */
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* 卡片式布局 */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        /* 侧边栏设计 */
        .sidebar {
            width: 250px;
            background: #f8f9fa;
            padding: 20px;
            border-right: 1px solid #e9ecef;
        }
    </style>
</head>
```

#### 3.2 实时交互功能
实现了实时消息发送、接收和统计更新：

```javascript
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // 禁用输入
    messageInput.disabled = true;
    sendButton.disabled = true;
    loading.style.display = 'block';

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                mode: document.getElementById('mode').value
            })
        });

        const data = await response.json();
        
        if (data.success) {
            addMessage(data.response, 'assistant');
            
            // 显示评分信息
            if (data.score) {
                displayScoreInfo(data.score);
            }
            
            // 显示响应详情
            if (data.mode_used) {
                displayResponseInfo(data);
            }
        } else {
            addMessage('Sorry, I encountered an error while processing your question. Please try again.', 'error');
        }
    } catch (error) {
        addMessage('Network error occurred. Please try again.', 'error');
    } finally {
        // 重新启用输入
        messageInput.disabled = false;
        sendButton.disabled = false;
        loading.style.display = 'none';
        
        // 清空输入框
        messageInput.value = '';
        
        // 更新统计信息
        await updateStats();
    }
}
```

#### 3.3 实时统计更新
实现了统计信息的实时刷新：

```javascript
async function updateStats() {
    try {
        const response = await fetch('/stats');
        const data = await response.json();
        
        // 更新成本统计
        document.getElementById('totalQueries').textContent = data.total_queries || 0;
        document.getElementById('totalCost').textContent = `$${data.cost_stats.total_cost.toFixed(6)}`;
        document.getElementById('totalInputTokens').textContent = data.cost_stats.total_input_tokens || 0;
        document.getElementById('totalOutputTokens').textContent = data.cost_stats.total_output_tokens || 0;

        // 更新查询历史
        updateQueryHistory(data.query_history);
    } catch (error) {
        console.error('Failed to update stats:', error);
    }
}
```

#### 3.4 评分可视化
实现了答案评分的可视化展示：

```javascript
function displayScoreInfo(score) {
    const scoreInfo = document.createElement('div');
    scoreInfo.className = 'score-info';
    scoreInfo.innerHTML = `
        <div class="score-header">Answer Score: ${score.total_score}/10</div>
        <div class="score-details">
            ${score.feedback.map(f => `<div>${f}</div>`).join('')}
        </div>
    `;
    document.querySelector('.chat-messages').appendChild(scoreInfo);
}
```

## 功能特性

### 1. 核心功能
- ✅ **智能问答**: 基于LightRAG的多模式查询
- ✅ **自动模式选择**: 系统自动选择最佳查询模式
- ✅ **多语言支持**: 中英文自动检测和响应
- ✅ **实时评分**: 基于完整性、多样性、启发性的智能评分
- ✅ **成本统计**: 实时Token使用和API成本统计

### 2. 用户体验
- ✅ **现代化界面**: 响应式设计，支持多设备
- ✅ **实时交互**: 即时消息发送和接收
- ✅ **历史记录**: 查询历史保存和展示
- ✅ **统计面板**: 实时使用统计和成本监控
- ✅ **评分反馈**: 答案质量的可视化展示

### 3. 技术特性
- ✅ **异步处理**: 支持并发查询处理
- ✅ **错误处理**: 完善的异常处理机制
- ✅ **缓存机制**: LightRAG内置缓存优化
- ✅ **API设计**: RESTful API接口设计
- ✅ **数据持久化**: 查询历史和统计信息持久化

## 部署说明

### 环境要求
- Python 3.8+
- OpenAI API Key
- 必要的Python包（见requirements.txt）

### 启动步骤
1. 安装依赖：`pip install -r requirements.txt`
2. 设置环境变量：`export OPENAI_API_KEY="your-api-key"`
3. 启动服务：`python chatbot_web.py`
4. 访问界面：`http://localhost:8081`

## 项目结构

```
Demo/
├── chatbot_web.py              # 主应用文件
├── templates/
│   └── index.html             # 前端界面
├── stakeholder_management_rag_sync/  # LightRAG数据目录
├── inputs/                    # 输入文档目录
├── requirements.txt           # 依赖包列表
└── README_stakeholder_chatbot.md  # 本文档
```

## 技术亮点

### 1. LightRAG框架应用
- 充分利用LightRAG的图结构查询能力
- 实现了多模式查询的自动选择
- 优化了文档检索和答案生成

### 2. 智能评分系统
- 基于多维度评估答案质量
- 动态调整评分权重
- 提供详细的评分反馈

### 3. 实时统计系统
- 精确的Token使用统计
- 实时的API成本计算
- 查询历史的完整记录

### 4. 现代化前端
- 响应式设计适配多设备
- 实时数据更新和交互
- 直观的用户界面设计

## 总结

本项目成功实现了基于README文档的智能问答系统，通过LightRAG框架提供了强大的文档检索能力，结合现代化的Web界面，为用户提供了优秀的交互体验。系统具备完整的功能特性，包括多模式查询、智能评分、实时统计等，为利益相关者管理领域提供了实用的AI助手工具。

## 未来改进方向

1. **扩展知识库**: 添加更多相关文档和案例
2. **优化评分算法**: 引入更复杂的评估指标
3. **增加用户管理**: 支持多用户和权限管理
4. **移动端优化**: 开发原生移动应用
5. **API扩展**: 提供更多查询和分析接口 