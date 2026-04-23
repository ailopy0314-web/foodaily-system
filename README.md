# Foodaily 内容生产系统

## 项目结构
```
├── foodaily-system.html    # 前端页面（独立HTML）
├── server/
│   ├── app.py              # Flask API 服务
│   ├── scraper.py          # 爬虫模块
│   └── requirements.txt    # Python 依赖
├── render.yaml             # Render 部署配置
├── Procfile                # 进程配置
└── .gitignore
```

## 部署步骤

### 1. 部署后端到 Render
1. 访问 https://render.com 注册/登录
2. 点击 "New" → "Web Service"
3. 连接 GitHub 仓库（选择此项目）
4. Render 会自动检测 render.yaml 配置
5. 点击 "Apply" 开始部署
6. 等待部署完成，获得 URL 如: https://foodaily-scraper.onrender.com

### 2. 部署前端到 Netlify
1. 访问 https://app.netlify.com/drop
2. 将 foodaily-system.html 拖入上传区
3. 获得 URL 如: https://xxx.netlify.app
4. 或使用 Netlify 自定义域名

### 3. 更新 API 地址
如果后端部署后的地址不是 foodaily-scraper.onrender.com，
需要修改 foodaily-system.html 中的 CLOUD_API 变量。

## 本地开发
```bash
cd server
pip install -r requirements.txt
python app.py
# 然后用浏览器打开 foodaily-system.html
```
