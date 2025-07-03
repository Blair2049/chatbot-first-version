# 🚀 Vercel部署指南

## 部署步骤

### 1. 注册Vercel账号
- 访问：https://vercel.com/signup
- 使用GitHub账号登录

### 2. 连接GitHub仓库
- 在Vercel控制台点击"New Project"
- 选择您的GitHub仓库
- 选择"chatbot第一版"文件夹

### 3. 配置环境变量
在Vercel项目设置中添加以下环境变量：

```
OPENAI_API_KEY=your_actual_openai_api_key_here
FLASK_ENV=production
FLASK_DEBUG=false
```

**⚠️ 重要安全提醒：**
- 不要将真实的API密钥写在代码中
- 只在Vercel控制台的环境变量中设置
- 确保.gitignore文件已正确配置

### 4. 部署设置
- Framework Preset: Other
- Build Command: 留空
- Output Directory: 留空
- Install Command: `pip install -r requirements.txt`

### 5. 部署
- 点击"Deploy"
- 等待部署完成
- 获得公网访问链接

## 安全特性
- ✅ 自动HTTPS
- ✅ 环境变量加密存储
- ✅ 全球CDN
- ✅ DDoS防护

## 注意事项
- 保持原有代码不变
- 所有功能完全保留
- 支持多语言问答
- 智能模式选择
- 实时统计和历史记录

## 访问链接
部署完成后，您将获得类似这样的链接：
`https://your-project-name.vercel.app`

任何人都可以通过这个链接访问您的chatbot！ 