"""
Foodaily 资讯爬虫模块
支持从多个食品行业信息源抓取最新资讯
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import json
import hashlib
import time
import logging
import warnings
from bs4 import XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 请求头，模拟浏览器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,ja;q=0.8,zh-CN;q=0.7',
}

# 超时设置
TIMEOUT = 15


def generate_id(title, source):
    """根据标题和来源生成唯一ID"""
    raw = f"{source}:{title}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()[:12]


def is_recent(date_str, hours=72):
    """检查日期是否在指定小时数内"""
    if not date_str:
        return True  # 没有日期的默认保留
    try:
        # 尝试多种日期格式
        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d', '%B %d, %Y', '%b %d, %Y',
                     '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%d %b %Y', '%d %B %Y']:
            try:
                pub_date = datetime.strptime(date_str.strip(), fmt)
                return (datetime.now() - pub_date).total_seconds() < hours * 3600
            except ValueError:
                continue
        return True  # 无法解析的默认保留
    except Exception:
        return True


# ============================================================
# 各网站专用爬虫
# ============================================================

def scrape_food_dive():
    """Food Dive - 北美食品行业深度"""
    items = []
    try:
        resp = requests.get('https://www.fooddive.com/', headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        # 抓取首页文章卡片
        articles = soup.select('article, .feed-item, [class*="article"], [class*="story"]')
        for art in articles[:15]:
            title_el = art.select_one('h2 a, h3 a, a[class*="title"], [class*="headline"] a')
            if not title_el:
                title_el = art.select_one('a[href*="/news/"]')
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            url = title_el.get('href', '')
            if url and not url.startswith('http'):
                url = 'https://www.fooddive.com' + url

            date_el = art.select_one('time, [class*="date"], [class*="time"], [class*="pub"]')
            date_str = date_el.get_text(strip=True) if date_el else ''
            if date_el and date_el.get('datetime'):
                date_str = date_el['datetime'][:10]

            summary_el = art.select_one('p, [class*="desc"], [class*="summary"], [class*="teaser"]')
            summary = summary_el.get_text(strip=True)[:100] if summary_el else ''

            items.append({
                'title': title,
                'date': date_str,
                'source': 'Food Dive',
                'url': url,
                'summary': summary,
                'category': '行业深度',
                'region': '北美',
            })

        logger.info(f"Food Dive: 抓取 {len(items)} 条")
    except Exception as e:
        logger.error(f"Food Dive 抓取失败: {e}")
    return items


def scrape_food_navigator_usa():
    """Food Navigator USA"""
    items = []
    try:
        resp = requests.get('https://www.foodnavigator-usa.com/', headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        articles = soup.select('article, [class*="article"], [class*="story"], [class*="news-item"]')
        for art in articles[:15]:
            title_el = art.select_one('h2 a, h3 a, a[class*="title"]')
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            url = title_el.get('href', '')
            if url and not url.startswith('http'):
                url = 'https://www.foodnavigator-usa.com' + url

            date_el = art.select_one('time, [class*="date"], [datetime]')
            date_str = ''
            if date_el:
                date_str = date_el.get('datetime', '')[:10] or date_el.get_text(strip=True)

            summary_el = art.select_one('p, [class*="desc"], [class*="summary"]')
            summary = summary_el.get_text(strip=True)[:100] if summary_el else ''

            items.append({
                'title': title,
                'date': date_str,
                'source': 'Food Navigator USA',
                'url': url,
                'summary': summary,
                'category': '行业导航',
                'region': '北美',
            })

        logger.info(f"Food Navigator USA: 抓取 {len(items)} 条")
    except Exception as e:
        logger.error(f"Food Navigator USA 抓取失败: {e}")
    return items


def scrape_food_business_news():
    """Food Business News"""
    items = []
    try:
        resp = requests.get('https://www.foodbusinessnews.net/', headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        articles = soup.select('article, [class*="article"], [class*="story"], [class*="item"]')
        for art in articles[:15]:
            title_el = art.select_one('h2 a, h3 a, h4 a, a[class*="title"]')
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            url = title_el.get('href', '')
            if url and not url.startswith('http'):
                url = 'https://www.foodbusinessnews.net' + url

            date_el = art.select_one('time, [class*="date"], [datetime]')
            date_str = ''
            if date_el:
                date_str = date_el.get('datetime', '')[:10] or date_el.get_text(strip=True)

            summary_el = art.select_one('p, [class*="desc"], [class*="summary"]')
            summary = summary_el.get_text(strip=True)[:100] if summary_el else ''

            items.append({
                'title': title,
                'date': date_str,
                'source': 'Food Business News',
                'url': url,
                'summary': summary,
                'category': '行业商业',
                'region': '北美',
            })

        logger.info(f"Food Business News: 抓取 {len(items)} 条")
    except Exception as e:
        logger.error(f"Food Business News 抓取失败: {e}")
    return items


def scrape_prepared_foods():
    """Prepared Foods"""
    items = []
    try:
        resp = requests.get('https://www.preparedfoods.com/', headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        articles = soup.select('article, [class*="article"], [class*="story"], [class*="content"]')
        for art in articles[:12]:
            title_el = art.select_one('h2 a, h3 a, a[class*="title"]')
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            url = title_el.get('href', '')
            if url and not url.startswith('http'):
                url = 'https://www.preparedfoods.com' + url

            date_el = art.select_one('time, [class*="date"], [datetime]')
            date_str = ''
            if date_el:
                date_str = date_el.get('datetime', '')[:10] or date_el.get_text(strip=True)

            summary_el = art.select_one('p, [class*="desc"], [class*="summary"]')
            summary = summary_el.get_text(strip=True)[:100] if summary_el else ''

            items.append({
                'title': title,
                'date': date_str,
                'source': 'Prepared Foods',
                'url': url,
                'summary': summary,
                'category': '行业技术',
                'region': '北美',
            })

        logger.info(f"Prepared Foods: 抓取 {len(items)} 条")
    except Exception as e:
        logger.error(f"Prepared Foods 抓取失败: {e}")
    return items


def scrape_foodbev():
    """Foodbev - 行业资讯"""
    items = []
    try:
        resp = requests.get('https://www.foodbev.com/', headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        articles = soup.select('article, [class*="article"], [class*="story"], [class*="post"]')
        for art in articles[:15]:
            title_el = art.select_one('h2 a, h3 a, a[class*="title"]')
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            url = title_el.get('href', '')
            if url and not url.startswith('http'):
                url = 'https://www.foodbev.com' + url

            date_el = art.select_one('time, [class*="date"], [datetime]')
            date_str = ''
            if date_el:
                date_str = date_el.get('datetime', '')[:10] or date_el.get_text(strip=True)

            summary_el = art.select_one('p, [class*="desc"], [class*="summary"], [class*="excerpt"]')
            summary = summary_el.get_text(strip=True)[:100] if summary_el else ''

            items.append({
                'title': title,
                'date': date_str,
                'source': 'Foodbev',
                'url': url,
                'summary': summary,
                'category': '行业资讯',
                'region': '北美',
            })

        logger.info(f"Foodbev: 抓取 {len(items)} 条")
    except Exception as e:
        logger.error(f"Foodbev 抓取失败: {e}")
    return items


def scrape_trend_hunter():
    """Trend Hunter - 趋势追踪"""
    items = []
    try:
        resp = requests.get('https://www.trendhunter.com/food', headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        articles = soup.select('article, [class*="article"], [class*="trend"], [class*="item"]')
        for art in articles[:12]:
            title_el = art.select_one('h2 a, h3 a, a[class*="title"]')
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            url = title_el.get('href', '')
            if url and not url.startswith('http'):
                url = 'https://www.trendhunter.com' + url

            date_el = art.select_one('time, [class*="date"]')
            date_str = date_el.get_text(strip=True) if date_el else ''

            summary_el = art.select_one('p, [class*="desc"], [class*="summary"]')
            summary = summary_el.get_text(strip=True)[:100] if summary_el else ''

            items.append({
                'title': title,
                'date': date_str,
                'source': 'Trend Hunter',
                'url': url,
                'summary': summary,
                'category': '趋势追踪',
                'region': '北美',
            })

        logger.info(f"Trend Hunter: 抓取 {len(items)} 条")
    except Exception as e:
        logger.error(f"Trend Hunter 抓取失败: {e}")
    return items


def scrape_just_food():
    """Just Food - 欧洲食品行业"""
    items = []
    try:
        resp = requests.get('https://www.just-food.com/', headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        articles = soup.select('article, [class*="article"], [class*="story"]')
        for art in articles[:12]:
            title_el = art.select_one('h2 a, h3 a, a[class*="title"]')
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            url = title_el.get('href', '')
            if url and not url.startswith('http'):
                url = 'https://www.just-food.com' + url

            date_el = art.select_one('time, [class*="date"], [datetime]')
            date_str = ''
            if date_el:
                date_str = date_el.get('datetime', '')[:10] or date_el.get_text(strip=True)

            summary_el = art.select_one('p, [class*="desc"]')
            summary = summary_el.get_text(strip=True)[:100] if summary_el else ''

            items.append({
                'title': title,
                'date': date_str,
                'source': 'Just Food',
                'url': url,
                'summary': summary,
                'category': '行业资讯',
                'region': '欧洲',
            })

        logger.info(f"Just Food: 抓取 {len(items)} 条")
    except Exception as e:
        logger.error(f"Just Food 抓取失败: {e}")
    return items


def scrape_food_navigator_eu():
    """Food Navigator Europe"""
    items = []
    try:
        resp = requests.get('https://www.foodnavigator.com/', headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        articles = soup.select('article, [class*="article"], [class*="story"]')
        for art in articles[:12]:
            title_el = art.select_one('h2 a, h3 a, a[class*="title"]')
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            url = title_el.get('href', '')
            if url and not url.startswith('http'):
                url = 'https://www.foodnavigator.com' + url

            date_el = art.select_one('time, [class*="date"], [datetime]')
            date_str = ''
            if date_el:
                date_str = date_el.get('datetime', '')[:10] or date_el.get_text(strip=True)

            summary_el = art.select_one('p, [class*="desc"]')
            summary = summary_el.get_text(strip=True)[:100] if summary_el else ''

            items.append({
                'title': title,
                'date': date_str,
                'source': 'Food Navigator EU',
                'url': url,
                'summary': summary,
                'category': '欧洲食品',
                'region': '欧洲',
            })

        logger.info(f"Food Navigator EU: 抓取 {len(items)} 条")
    except Exception as e:
        logger.error(f"Food Navigator EU 抓取失败: {e}")
    return items


def scrape_nutraingredients():
    """NutraIngredients - 营养配料"""
    items = []
    try:
        resp = requests.get('https://www.nutraingredients.com/', headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        articles = soup.select('article, [class*="article"], [class*="story"]')
        for art in articles[:12]:
            title_el = art.select_one('h2 a, h3 a, a[class*="title"]')
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            url = title_el.get('href', '')
            if url and not url.startswith('http'):
                url = 'https://www.nutraingredients.com' + url

            date_el = art.select_one('time, [class*="date"], [datetime]')
            date_str = ''
            if date_el:
                date_str = date_el.get('datetime', '')[:10] or date_el.get_text(strip=True)

            summary_el = art.select_one('p, [class*="desc"]')
            summary = summary_el.get_text(strip=True)[:100] if summary_el else ''

            items.append({
                'title': title,
                'date': date_str,
                'source': 'NutraIngredients',
                'url': url,
                'summary': summary,
                'category': '营养配料',
                'region': '欧洲',
            })

        logger.info(f"NutraIngredients: 抓取 {len(items)} 条")
    except Exception as e:
        logger.error(f"NutraIngredients 抓取失败: {e}")
    return items


def scrape_dairy_reporter():
    """Dairy Reporter - 乳制品"""
    items = []
    try:
        resp = requests.get('https://www.dairyreporter.com/', headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        articles = soup.select('article, [class*="article"], [class*="story"]')
        for art in articles[:10]:
            title_el = art.select_one('h2 a, h3 a, a[class*="title"]')
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            url = title_el.get('href', '')
            if url and not url.startswith('http'):
                url = 'https://www.dairyreporter.com' + url

            date_el = art.select_one('time, [class*="date"], [datetime]')
            date_str = ''
            if date_el:
                date_str = date_el.get('datetime', '')[:10] or date_el.get_text(strip=True)

            summary_el = art.select_one('p, [class*="desc"]')
            summary = summary_el.get_text(strip=True)[:100] if summary_el else ''

            items.append({
                'title': title,
                'date': date_str,
                'source': 'Dairy Reporter',
                'url': url,
                'summary': summary,
                'category': '乳制品',
                'region': '欧洲',
            })

        logger.info(f"Dairy Reporter: 抓取 {len(items)} 条")
    except Exception as e:
        logger.error(f"Dairy Reporter 抓取失败: {e}")
    return items


def scrape_beverage_daily():
    """Beverage Daily - 饮料行业"""
    items = []
    try:
        resp = requests.get('https://www.beveragedaily.com/', headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        articles = soup.select('article, [class*="article"], [class*="story"]')
        for art in articles[:10]:
            title_el = art.select_one('h2 a, h3 a, a[class*="title"]')
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            url = title_el.get('href', '')
            if url and not url.startswith('http'):
                url = 'https://www.beveragedaily.com' + url

            date_el = art.select_one('time, [class*="date"], [datetime]')
            date_str = ''
            if date_el:
                date_str = date_el.get('datetime', '')[:10] or date_el.get_text(strip=True)

            summary_el = art.select_one('p, [class*="desc"]')
            summary = summary_el.get_text(strip=True)[:100] if summary_el else ''

            items.append({
                'title': title,
                'date': date_str,
                'source': 'Beverage Daily',
                'url': url,
                'summary': summary,
                'category': '饮料行业',
                'region': '欧洲',
            })

        logger.info(f"Beverage Daily: 抓取 {len(items)} 条")
    except Exception as e:
        logger.error(f"Beverage Daily 抓取失败: {e}")
    return items


def scrape_pr_newswire_food():
    """Cision PR Newswire - 食品相关新闻稿"""
    items = []
    try:
        resp = requests.get('https://www.prnewswire.com/news-releases/food-beverages/', headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        articles = soup.select('[class*="release"], article, [class*="story"]')
        for art in articles[:15]:
            title_el = art.select_one('h2 a, h3 a, a[class*="title"], a[href*="/news-releases/"]')
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            url = title_el.get('href', '')
            if url and not url.startswith('http'):
                url = 'https://www.prnewswire.com' + url

            date_el = art.select_one('time, [class*="date"], [class*="timestamp"], [datetime]')
            date_str = ''
            if date_el:
                date_str = date_el.get('datetime', '')[:10] or date_el.get_text(strip=True)[:20]

            summary_el = art.select_one('p, [class*="desc"], [class*="summary"]')
            summary = summary_el.get_text(strip=True)[:100] if summary_el else ''

            items.append({
                'title': title,
                'date': date_str,
                'source': 'PR Newswire',
                'url': url,
                'summary': summary,
                'category': '新闻稿',
                'region': '北美',
            })

        logger.info(f"PR Newswire: 抓取 {len(items)} 条")
    except Exception as e:
        logger.error(f"PR Newswire 抓取失败: {e}")
    return items


def scrape_mognavi():
    """Mognavi - 日本新品&评测"""
    items = []
    try:
        resp = requests.get('https://mognavi.jp/do/whats_new/show', headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        articles = soup.select('[class*="item"], [class*="product"], [class*="new"], article')
        for art in articles[:15]:
            title_el = art.select_one('h2 a, h3 a, a[class*="title"], a[class*="name"]')
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            url = title_el.get('href', '')
            if url and not url.startswith('http'):
                url = 'https://mognavi.jp' + url

            date_el = art.select_one('time, [class*="date"]')
            date_str = date_el.get_text(strip=True) if date_el else ''

            summary_el = art.select_one('p, [class*="desc"]')
            summary = summary_el.get_text(strip=True)[:100] if summary_el else ''

            items.append({
                'title': title,
                'date': date_str,
                'source': 'Mognavi',
                'url': url,
                'summary': summary,
                'category': '新品发布',
                'region': '日本',
            })

        logger.info(f"Mognavi: 抓取 {len(items)} 条")
    except Exception as e:
        logger.error(f"Mognavi 抓取失败: {e}")
    return items


def scrape_nikkei_xtrend():
    """日経クロストレンド - 日本综合分析"""
    items = []
    try:
        resp = requests.get('https://xtrend.nikkei.com/', headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        articles = soup.select('article, [class*="article"], [class*="story"], [class*="item"]')
        for art in articles[:12]:
            title_el = art.select_one('h2 a, h3 a, a[class*="title"]')
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            url = title_el.get('href', '')
            if url and not url.startswith('http'):
                url = 'https://xtrend.nikkei.com' + url

            date_el = art.select_one('time, [class*="date"], [datetime]')
            date_str = ''
            if date_el:
                date_str = date_el.get('datetime', '')[:10] or date_el.get_text(strip=True)

            summary_el = art.select_one('p, [class*="desc"]')
            summary = summary_el.get_text(strip=True)[:100] if summary_el else ''

            items.append({
                'title': title,
                'date': date_str,
                'source': '日経クロストレンド',
                'url': url,
                'summary': summary,
                'category': '综合分析',
                'region': '日本',
            })

        logger.info(f"日経クロストレンド: 抓取 {len(items)} 条")
    except Exception as e:
        logger.error(f"日経クロストレンド 抓取失败: {e}")
    return items


# ============================================================
# 国内食品行业网站爬虫
# ============================================================

def scrape_fbif():
    """FBIF 食品商业 - 国内A+级"""
    items = []
    try:
        resp = requests.get('https://www.fbif.cn/', headers={
            **HEADERS,
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        articles = soup.select('article, [class*="article"], [class*="post"], [class*="item"]')
        for art in articles[:15]:
            title_el = art.select_one('h2 a, h3 a, a[class*="title"]')
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 6:
                continue

            url = title_el.get('href', '')
            if url and not url.startswith('http'):
                url = 'https://www.fbif.cn' + url

            date_el = art.select_one('time, [class*="date"], [datetime]')
            date_str = ''
            if date_el:
                date_str = date_el.get('datetime', '')[:10] or date_el.get_text(strip=True)

            summary_el = art.select_one('p, [class*="desc"], [class*="summary"]')
            summary = summary_el.get_text(strip=True)[:100] if summary_el else ''

            items.append({
                'title': title,
                'date': date_str,
                'source': 'FBIF',
                'url': url,
                'summary': summary,
                'category': '食品商业',
                'region': '国内',
            })

        logger.info(f"FBIF: 抓取 {len(items)} 条")
    except Exception as e:
        logger.error(f"FBIF 抓取失败: {e}")
    return items


def scrape_foodmate():
    """食品伙伴网 - 国内行业资讯"""
    items = []
    try:
        resp = requests.get('https://www.foodmate.net/', headers={
            **HEADERS,
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        articles = soup.select('article, [class*="article"], [class*="news"], [class*="item"]')
        for art in articles[:12]:
            title_el = art.select_one('h2 a, h3 a, h4 a, a[class*="title"]')
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 6:
                continue

            url = title_el.get('href', '')
            if url and not url.startswith('http'):
                url = 'https://www.foodmate.net' + url

            date_el = art.select_one('time, [class*="date"], [datetime], [class*="time"]')
            date_str = date_el.get_text(strip=True) if date_el else ''

            summary_el = art.select_one('p, [class*="desc"]')
            summary = summary_el.get_text(strip=True)[:100] if summary_el else ''

            items.append({
                'title': title,
                'date': date_str,
                'source': '食品伙伴网',
                'url': url,
                'summary': summary,
                'category': '行业资讯',
                'region': '国内',
            })

        logger.info(f"食品伙伴网: 抓取 {len(items)} 条")
    except Exception as e:
        logger.error(f"食品伙伴网 抓取失败: {e}")
    return items


def scrape_cnfood():
    """中国食品报 - 国内食品行业"""
    items = []
    try:
        resp = requests.get('https://www.cnfood.cn/', headers={
            **HEADERS,
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        articles = soup.select('article, [class*="article"], [class*="news"], [class*="item"]')
        for art in articles[:12]:
            title_el = art.select_one('h2 a, h3 a, h4 a, a[class*="title"]')
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 6:
                continue

            url = title_el.get('href', '')
            if url and not url.startswith('http'):
                url = 'https://www.cnfood.cn' + url

            date_el = art.select_one('time, [class*="date"]')
            date_str = date_el.get_text(strip=True) if date_el else ''

            summary_el = art.select_one('p, [class*="desc"]')
            summary = summary_el.get_text(strip=True)[:100] if summary_el else ''

            items.append({
                'title': title,
                'date': date_str,
                'source': '中国食品报',
                'url': url,
                'summary': summary,
                'category': '行业资讯',
                'region': '国内',
            })

        logger.info(f"中国食品报: 抓取 {len(items)} 条")
    except Exception as e:
        logger.error(f"中国食品报 抓取失败: {e}")
    return items


# ============================================================
# RSS 爬虫（适用于支持RSS的网站）
# ============================================================

def scrape_rss(feed_url, source_name, category, region):
    """通用RSS爬虫"""
    items = []
    try:
        resp = requests.get(feed_url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'xml')

        entries = soup.find_all('item') or soup.find_all('entry')
        for entry in entries[:10]:
            title_el = entry.find('title')
            link_el = entry.find('link')
            date_el = entry.find('pubDate') or entry.find('published') or entry.find('updated')
            desc_el = entry.find('description') or entry.find('summary') or entry.find('content')

            title = title_el.get_text(strip=True) if title_el else ''
            if not title or len(title) < 10:
                continue

            url = ''
            if link_el:
                url = link_el.get('href', '') or link_el.get_text(strip=True)

            date_str = ''
            if date_el:
                date_str = date_el.get_text(strip=True)[:16]

            summary = ''
            if desc_el:
                # 清理HTML标签
                raw = desc_el.get_text(strip=True)
                summary = re.sub(r'<[^>]+>', '', raw)[:100]

            items.append({
                'title': title,
                'date': date_str,
                'source': source_name,
                'url': url,
                'summary': summary,
                'category': category,
                'region': region,
            })

        logger.info(f"RSS {source_name}: 抓取 {len(items)} 条")
    except Exception as e:
        logger.error(f"RSS {source_name} 抓取失败: {e}")
    return items


# ============================================================
# 主抓取入口
# ============================================================

# 所有爬虫任务
SCRAPERS = [
    # A+ 级信息源（优先抓取）
    scrape_food_dive,
    scrape_foodbev,
    scrape_prepared_foods,
    scrape_food_business_news,
    scrape_food_navigator_usa,
    # A 级信息源
    scrape_trend_hunter,
    scrape_mognavi,
    scrape_nikkei_xtrend,
    # 欧洲信息源
    scrape_just_food,
    scrape_food_navigator_eu,
    scrape_nutraingredients,
    scrape_dairy_reporter,
    scrape_beverage_daily,
    # 国内信息源
    scrape_fbif,
    scrape_foodmate,
    scrape_cnfood,
]

# RSS feeds（部分网站支持RSS，更可靠）
RSS_FEEDS = [
    ('https://www.fooddive.com/feeds/news', 'Food Dive RSS', '行业深度', '北美'),
    ('https://www.just-food.com/rss.aspx', 'Just Food RSS', '行业资讯', '欧洲'),
    ('https://feeds.feedburner.com/foodnavigator', 'Food Navigator RSS', '行业导航', '欧洲'),
    ('https://www.foodnavigator-usa.com/feeds/latest.rss', 'Food Navigator USA RSS', '行业导航', '北美'),
    ('https://www.foodbusinessnews.net/Articles/RSS', 'Food Business News RSS', '行业商业', '北美'),
    ('https://www.nutraingredients-usa.com/feeds/latest.rss', 'NutraIngredients USA RSS', '营养配料', '北美'),
    ('https://www.beveragedaily.com/feeds/latest.rss', 'Beverage Daily RSS', '饮料行业', '欧洲'),
    ('https://www.dairyreporter.com/feeds/latest.rss', 'Dairy Reporter RSS', '乳制品', '欧洲'),
    ('https://www.confectionerynews.com/feeds/latest.rss', 'Confectionery News RSS', '糖巧行业', '欧洲'),
    # 国内RSS
    ('https://www.fbif.cn/rss', 'FBIF RSS', '食品商业', '国内'),
    ('https://www.foodmate.net/rss', '食品伙伴网 RSS', '行业资讯', '国内'),
]


def deduplicate(items):
    """去重：标题相似度>80%的只保留一个"""
    seen = []
    result = []
    for item in items:
        title_lower = item['title'].lower().strip()
        is_dup = False
        for s in seen:
            # 简单相似度：共同词占比
            words_a = set(title_lower.split())
            words_b = set(s.split())
            if not words_a or not words_b:
                continue
            overlap = len(words_a & words_b) / max(len(words_a), len(words_b))
            if overlap > 0.7:
                is_dup = True
                break
        if not is_dup:
            seen.append(title_lower)
            result.append(item)
    return result


def run_all_scrapers(use_rss=True):
    """执行所有爬虫，返回合并去重后的结果"""
    all_items = []

    # 先抓RSS（更稳定）
    if use_rss:
        for feed_url, name, cat, region in RSS_FEEDS:
            items = scrape_rss(feed_url, name, cat, region)
            all_items.extend(items)
            time.sleep(0.5)  # 礼貌性延迟

    # 再跑HTML爬虫
    for scraper in SCRAPERS:
        try:
            items = scraper()
            all_items.extend(items)
        except Exception as e:
            logger.error(f"爬虫 {scraper.__name__} 异常: {e}")
        time.sleep(0.5)

    # 添加唯一ID
    for item in all_items:
        item['id'] = generate_id(item['title'], item['source'])

    # 去重
    all_items = deduplicate(all_items)

    # 按日期排序（新的在前）
    all_items.sort(key=lambda x: x.get('date', ''), reverse=True)

    logger.info(f"总计抓取 {len(all_items)} 条去重后资讯")
    return all_items


if __name__ == '__main__':
    # 测试运行
    results = run_all_scrapers()
    for r in results[:5]:
        print(f"[{r['source']}] {r['title'][:60]}")
    print(f"\n共 {len(results)} 条")
