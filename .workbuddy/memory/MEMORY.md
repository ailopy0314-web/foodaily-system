# MEMORY.md - 长期记忆

## 用户项目
- **Foodaily 内容生产系统**：4角色食品行业内容生产流程（资讯侦察员→选题策划专家→内容写手→合规审核员）
  - 系统页面：foodaily-system.html
  - Python后端：server/app.py（Flask API）+ server/scraper.py（爬虫模块）
  - 稳定数据源：Food Dive RSS, Just Food RSS, Food Dive HTML, Just Food HTML
  - 一键启动：启动服务.bat（先启后端，再开前端HTML）
  - 前端自动检测后端：绿点=真实数据，黄点=模拟数据fallback
  - 英文标题自动分类+中文Foodaily风格改写
  - **线上地址**：
    - 前端：https://foodaily-title-news.netlify.app
    - 后端：https://foodaily-system.onrender.com（Render免费版，冷启动30-50秒）
    - GitHub：https://github.com/ailopy0314-web/foodaily-system
  - 新增数据来源管理：前端可查看/新增/删除来源，后端通用爬虫自动检测RSS/HTML
  - 自定义来源持久化保存，刷新选题时自动抓取
