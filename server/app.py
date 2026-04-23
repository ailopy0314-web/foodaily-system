"""
Foodaily 内容生产系统 - Flask API 服务器
提供真实资讯抓取接口，供前端调用
支持部署到 Render / Railway 等云平台
"""

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from scraper import run_all_scrapers, SCRAPERS, RSS_FEEDS
import threading
import time
import logging

app = Flask(__name__)

# 允许所有来源跨域（部署到云端后，任何网页都能调用）
CORS(app, resources={r"/api/*": {"origins": "*"}})

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 缓存：避免频繁抓取
cache = {
    'items': [],
    'last_scrape': 0,
    'scraping': False,
    'scrape_progress': '',
}

CACHE_TTL = int(os.environ.get('CACHE_TTL', 1800))  # 默认30分钟，可通过环境变量调整


@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'scrapers': len(SCRAPERS),
        'rss_feeds': len(RSS_FEEDS),
        'cached_items': len(cache['items']),
        'last_scrape': cache['last_scrape'],
        'scraping': cache['scraping'],
        'env': os.environ.get('FLASK_ENV', 'production'),
    })


@app.route('/api/scrape', methods=['POST'])
def scrape():
    """触发一次完整抓取"""
    force = request.args.get('force', '0') == '1'

    # 如果正在抓取中，返回进度
    if cache['scraping']:
        return jsonify({
            'status': 'scraping',
            'message': '正在抓取中...',
            'progress': cache['scrape_progress'],
            'cached_items': len(cache['items']),
        })

    # 如果缓存未过期且不强制刷新
    if not force and cache['items'] and (time.time() - cache['last_scrape']) < CACHE_TTL:
        return jsonify({
            'status': 'cached',
            'message': f'返回缓存数据（{len(cache["items"])}条，缓存于{int(cache["last_scrape"])}）',
            'items': cache['items'],
            'total': len(cache['items']),
        })

    # 后台启动抓取
    def do_scrape():
        cache['scraping'] = True
        cache['scrape_progress'] = '开始抓取...'
        try:
            items = run_all_scrapers(use_rss=True)
            cache['items'] = items
            cache['last_scrape'] = time.time()
            cache['scrape_progress'] = f'完成，共{len(items)}条'
        except Exception as e:
            cache['scrape_progress'] = f'抓取失败: {str(e)}'
            logger.error(f"抓取异常: {e}")
        finally:
            cache['scraping'] = False

    thread = threading.Thread(target=do_scrape, daemon=True)
    thread.start()

    return jsonify({
        'status': 'started',
        'message': '抓取已启动，请稍后调用 /api/status 查看进度',
    })


@app.route('/api/status', methods=['GET'])
def status():
    """查看抓取进度"""
    return jsonify({
        'scraping': cache['scraping'],
        'progress': cache['scrape_progress'],
        'cached_items': len(cache['items']),
        'last_scrape': cache['last_scrape'],
    })


@app.route('/api/news', methods=['GET'])
def get_news():
    """获取缓存的新闻列表"""
    # 如果缓存为空，自动触发一次抓取
    if not cache['items'] and not cache['scraping']:
        # 同步抓取（首次）
        cache['scraping'] = True
        cache['scrape_progress'] = '首次抓取中...'
        try:
            items = run_all_scrapers(use_rss=True)
            cache['items'] = items
            cache['last_scrape'] = time.time()
            cache['scrape_progress'] = f'完成，共{len(items)}条'
        except Exception as e:
            cache['scrape_progress'] = f'抓取失败: {str(e)}'
        finally:
            cache['scraping'] = False

    # 支持分页和筛选
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    region = request.args.get('region', '')
    source = request.args.get('source', '')

    items = cache['items']

    # 筛选
    if region:
        items = [i for i in items if i.get('region') == region]
    if source:
        items = [i for i in items if source.lower() in i.get('source', '').lower()]

    # 分页
    start = (page - 1) * per_page
    end = start + per_page
    paginated = items[start:end]

    return jsonify({
        'items': paginated,
        'total': len(items),
        'page': page,
        'per_page': per_page,
        'last_scrape': cache['last_scrape'],
        'scraping': cache['scraping'],
    })


@app.route('/api/sources', methods=['GET'])
def get_sources():
    """获取所有信息源列表"""
    sources = []
    for scraper in SCRAPERS:
        sources.append({
            'name': scraper.__name__,
            'type': 'html',
        })
    for feed_url, name, cat, region in RSS_FEEDS:
        sources.append({
            'name': name,
            'url': feed_url,
            'type': 'rss',
            'category': cat,
            'region': region,
        })
    return jsonify({'sources': sources})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 50)
    print("🚀 Foodaily 资讯抓取服务启动")
    print("=" * 50)
    print(f"📡 爬虫数量: {len(SCRAPERS)} 个HTML爬虫 + {len(RSS_FEEDS)} 个RSS源")
    print(f"🌐 API 地址: http://localhost:{port}")
    print(f"📋 接口列表:")
    print(f"  GET  /api/health   - 健康检查")
    print(f"  POST /api/scrape   - 触发抓取")
    print(f"  GET  /api/status   - 查看进度")
    print(f"  GET  /api/news     - 获取新闻")
    print(f"  GET  /api/sources  - 信息源列表")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=True)
