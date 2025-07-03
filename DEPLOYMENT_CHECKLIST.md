# 部署清单 - 需要上传到GitHub的文件

## ✅ 必需上传的核心文件

### 1. 应用代码文件
- [ ] `chatbot_web.py` - 主应用文件
- [ ] `api.py` - Vercel适配文件
- [ ] `requirements.txt` - Python依赖
- [ ] `vercel.json` - Vercel配置

### 2. 前端文件
- [ ] `templates/index.html` - Web界面

### 3. 数据文件（重要！）
- [ ] `stakeholder_management_rag_sync/` - 整个文件夹
  - [ ] `graph_chunk_entity_relation.graphml` (2.5MB)
  - [ ] `kv_store_full_docs.json` (1.4MB)
  - [ ] `kv_store_text_chunks.json` (1.6MB)
  - [ ] `kv_store_llm_response_cache.json` (19MB)
  - [ ] `kv_store_doc_status.json` (3.9KB)
  - [ ] `vdb_chunks.json` (2.7MB)
  - [ ] `vdb_entities.json` (35MB)
  - [ ] `vdb_relationships.json` (24MB)

### 4. 文档文件
- [ ] `README.md` - 项目说明
- [ ] `deploy_vercel.md` - 部署指南
- [ ] `env_example.txt` - 环境变量示例

## ❌ 不要上传的文件

### 1. 敏感信息文件
- [ ] `.env` - 包含API密钥（如果存在）
- [ ] `*.log` - 日志文件
- [ ] `__pycache__/` - Python缓存

### 2. 开发文件
- [ ] `run_local.sh` - 本地开发脚本
- [ ] `setup_env.sh` - 环境设置脚本
- [ ] `stakeholder_management_chatbot_sync.py` - 开发版本
- [ ] `README_stakeholder_chatbot.md` - 详细开发文档
- [ ] `SECURITY_CHECKLIST.md` - 安全清单

## 📋 部署步骤

### 1. 创建新的GitHub仓库
```bash
# 在GitHub上创建新仓库
# 不要初始化README、.gitignore或license
```

### 2. 初始化本地仓库
```bash
cd chatbot第一版
git init
git add .
git commit -m "Initial commit: Stakeholder Management Chatbot"
```

### 3. 推送到GitHub
```bash
git remote add origin https://github.com/你的用户名/你的仓库名.git
git branch -M main
git push -u origin main
```

### 4. 部署到Vercel
```bash
# 安装Vercel CLI
npm install -g vercel

# 登录Vercel
vercel login

# 部署
vercel --prod
```

## ⚠️ 注意事项

1. **文件大小**: 数据文件总计约87MB，GitHub支持但上传可能较慢
2. **API密钥**: 确保.env文件在.gitignore中，不要上传
3. **环境变量**: 在Vercel控制台设置OPENAI_API_KEY
4. **依赖**: 确保requirements.txt包含所有必要依赖

## 🔧 故障排除

### 如果上传失败
- 检查文件大小限制
- 确保.gitignore正确配置
- 分批上传大文件

### 如果部署失败
- 检查Vercel日志
- 确认环境变量设置
- 验证requirements.txt 