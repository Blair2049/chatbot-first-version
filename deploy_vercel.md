# Vercel部署指南

## 1. 准备工作

### 1.1 安装Vercel CLI
```bash
npm install -g vercel
```

### 1.2 登录Vercel
```bash
vercel login
```

## 2. 环境变量设置

### 2.1 在Vercel控制台设置环境变量
1. 登录 [Vercel控制台](https://vercel.com/dashboard)
2. 选择你的项目
3. 进入 "Settings" → "Environment Variables"
4. 添加以下环境变量：

```
OPENAI_API_KEY = your_actual_openai_api_key
FLASK_ENV = production
FLASK_DEBUG = false
SECRET_KEY = your_random_secret_key
```

### 2.2 安全注意事项
- ✅ 永远不要在代码中硬编码API密钥
- ✅ 使用Vercel的环境变量功能
- ✅ 定期轮换API密钥
- ✅ 设置API密钥使用限制

## 3. 部署步骤

### 3.1 本地部署测试
```bash
# 设置环境变量
export OPENAI_API_KEY="your_api_key"
export FLASK_ENV="production"

# 测试运行
python chatbot_web.py
```

### 3.2 部署到Vercel
```bash
# 在项目根目录执行
vercel

# 或者直接部署到生产环境
vercel --prod
```

## 4. 部署后配置

### 4.1 域名设置
- Vercel会自动分配一个域名
- 可以在控制台设置自定义域名

### 4.2 监控和日志
- 在Vercel控制台查看部署日志
- 监控API使用情况和成本

## 5. 安全最佳实践

### 5.1 API密钥保护
- 使用环境变量存储敏感信息
- 定期检查API使用情况
- 设置OpenAI API使用限制

### 5.2 应用安全
- 启用HTTPS
- 设置适当的CORS策略
- 限制请求频率

## 6. 故障排除

### 6.1 常见问题
1. **环境变量未设置**: 检查Vercel控制台的环境变量配置
2. **依赖问题**: 确保requirements.txt包含所有依赖
3. **路径问题**: 确保文件路径正确

### 6.2 调试方法
- 查看Vercel部署日志
- 使用本地测试环境
- 检查环境变量是否正确加载

## 7. 维护和更新

### 7.1 代码更新
```bash
# 推送代码到GitHub
git add .
git commit -m "Update chatbot"
git push

# Vercel会自动重新部署
```

### 7.2 环境变量更新
- 在Vercel控制台更新环境变量
- 重新部署应用

## 8. 成本控制

### 8.1 OpenAI API成本
- 监控API使用情况
- 设置使用限制
- 优化提示词减少token使用

### 8.2 Vercel成本
- 免费计划通常足够
- 监控带宽使用情况 