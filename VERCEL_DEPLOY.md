# Vercel部署指南

## 部署步骤

### 1. 安装Vercel CLI
```bash
npm install -g vercel
```

### 2. 登录Vercel
```bash
vercel login
```

### 3. 在项目根目录部署
```bash
cd chatbot第一版
vercel
```

### 4. 设置环境变量
在Vercel控制台中设置以下环境变量：
- `OPENAI_API_KEY`: 您的OpenAI API密钥

### 5. 重新部署
```bash
vercel --prod
```

## 项目结构
```
chatbot第一版/
├── api/
│   └── index.py          # Vercel入口文件
├── chatbot_web.py        # 主Flask应用
├── requirements.txt      # Python依赖
├── vercel.json          # Vercel配置
└── ...
```

## 注意事项
- 确保所有依赖都在requirements.txt中
- 环境变量必须在Vercel控制台中设置
- 首次部署可能需要几分钟时间
- 如果遇到超时问题，可以调整vercel.json中的maxDuration

## 访问地址
部署成功后，您将获得一个类似以下的URL：
`https://your-project-name.vercel.app`

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