"""
简化版API文件，用于调试Vercel部署问题
"""
import os
import json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/index.html')
def index_html():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """聊天接口 - 简化版"""
    try:
        data = request.get_json()
        question = data.get('message', '')
        
        if not question.strip():
            return jsonify({'success': False, 'error': '问题不能为空'})
        
        # 检查环境变量
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return jsonify({
                'success': False, 
                'error': 'OPENAI_API_KEY 环境变量未设置',
                'debug': '请在Vercel控制台设置环境变量'
            })
        
        # 简化响应（用于测试）
        response = f"收到你的问题：{question}\n\n这是一个测试响应，说明API接口正常工作。\n\n环境变量检查：{'✅ 已设置' if api_key else '❌ 未设置'}"
        
        return jsonify({
            'success': True,
            'response': response,
            'mode_used': 'test',
            'score': {
                'total_score': 8.0,
                'comprehensiveness': 8.0,
                'diversity': 8.0,
                'empowerment': 8.0,
                'feedback': ['✅ 测试模式', '✅ API正常']
            },
            'cost': {
                'total_cost': 0.0,
                'llm_input_cost': 0.0,
                'llm_output_cost': 0.0,
                'embedding_cost': 0.0
            },
            'tokens': {
                'input_tokens': 0,
                'output_tokens': 0
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'API错误: {str(e)}',
            'debug': '请检查服务器日志'
        })

@app.route('/stats')
def get_stats():
    """统计信息接口 - 简化版"""
    try:
        return jsonify({
            'cost_stats': {
                'total_cost': 0.0,
                'total_input_tokens': 0,
                'total_output_tokens': 0,
                'total_embedding_tokens': 0
            },
            'query_history': [],
            'total_queries': 0,
            'status': 'debug_mode'
        })
    except Exception as e:
        return jsonify({
            'error': f'Stats API错误: {str(e)}',
            'status': 'error'
        })

@app.route('/health')
def health():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'api_key_set': bool(os.getenv("OPENAI_API_KEY")),
        'environment': os.getenv("VERCEL_ENV", "unknown")
    })

@app.route('/test')
def test():
    """测试接口"""
    return jsonify({
        'message': 'API服务器正常运行',
        'timestamp': '2024-01-01T00:00:00Z',
        'version': 'debug-1.0'
    })

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8081) 