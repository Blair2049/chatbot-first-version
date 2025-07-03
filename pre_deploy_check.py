#!/usr/bin/env python3
"""
部署前检查脚本
检查所有必要的文件和配置是否正确
"""

import os
import json
import sys

def check_file_exists(filepath, description):
    """检查文件是否存在"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - 文件不存在")
        return False

def check_file_size(filepath, max_size_mb=100):
    """检查文件大小"""
    if os.path.exists(filepath):
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        if size_mb > max_size_mb:
            print(f"⚠️  文件过大: {filepath} ({size_mb:.1f}MB > {max_size_mb}MB)")
            return False
        else:
            print(f"✅ 文件大小正常: {filepath} ({size_mb:.1f}MB)")
            return True
    return False

def check_json_file(filepath):
    """检查JSON文件格式"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            json.load(f)
        print(f"✅ JSON格式正确: {filepath}")
        return True
    except Exception as e:
        print(f"❌ JSON格式错误: {filepath} - {e}")
        return False

def main():
    print("🔍 开始部署前检查...\n")
    
    # 检查核心文件
    core_files = [
        ("api.py", "Vercel适配文件"),
        ("vercel.json", "Vercel配置文件"),
        ("requirements.txt", "Python依赖文件"),
        ("templates/index.html", "前端界面文件"),
        ("README.md", "项目说明文件"),
    ]
    
    core_files_ok = True
    for filepath, description in core_files:
        if not check_file_exists(filepath, description):
            core_files_ok = False
    
    print("\n📁 检查数据文件...")
    
    # 检查数据文件夹
    rag_dir = "stakeholder_management_rag_sync"
    if not check_file_exists(rag_dir, "RAG数据文件夹"):
        core_files_ok = False
    else:
        # 检查数据文件
        data_files = [
            "graph_chunk_entity_relation.graphml",
            "kv_store_full_docs.json",
            "kv_store_text_chunks.json",
            "kv_store_llm_response_cache.json",
            "kv_store_doc_status.json",
            "vdb_chunks.json",
            "vdb_entities.json",
            "vdb_relationships.json"
        ]
        
        for filename in data_files:
            filepath = os.path.join(rag_dir, filename)
            if filename.endswith('.json'):
                check_json_file(filepath)
            check_file_size(filepath, 100)  # 100MB限制
    
    print("\n🔧 检查配置文件...")
    
    # 检查vercel.json
    try:
        with open('vercel.json', 'r') as f:
            vercel_config = json.load(f)
        
        required_keys = ['version', 'builds', 'routes']
        for key in required_keys:
            if key in vercel_config:
                print(f"✅ vercel.json包含{key}")
            else:
                print(f"❌ vercel.json缺少{key}")
                core_files_ok = False
    except Exception as e:
        print(f"❌ vercel.json格式错误: {e}")
        core_files_ok = False
    
    # 检查requirements.txt
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        required_packages = ['flask', 'numpy', 'tiktoken', 'openai']
        for package in required_packages:
            if package in requirements:
                print(f"✅ requirements.txt包含{package}")
            else:
                print(f"❌ requirements.txt缺少{package}")
                core_files_ok = False
    except Exception as e:
        print(f"❌ requirements.txt读取错误: {e}")
        core_files_ok = False
    
    print("\n🔒 检查安全配置...")
    
    # 检查.gitignore
    if check_file_exists('.gitignore', '.gitignore文件'):
        with open('.gitignore', 'r') as f:
            gitignore_content = f.read()
        
        sensitive_patterns = ['.env', '*.log', '__pycache__', '*.pyc']
        for pattern in sensitive_patterns:
            if pattern in gitignore_content:
                print(f"✅ .gitignore包含{pattern}")
            else:
                print(f"⚠️  .gitignore缺少{pattern}")
    
    print("\n📊 检查结果总结...")
    
    if core_files_ok:
        print("✅ 所有核心文件检查通过！")
        print("✅ 可以安全部署到Vercel")
        print("\n📝 下一步操作:")
        print("1. 提交代码到GitHub")
        print("2. 在Vercel控制台设置环境变量OPENAI_API_KEY")
        print("3. 部署到Vercel")
        return True
    else:
        print("❌ 发现一些问题，请修复后再部署")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 