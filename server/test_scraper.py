"""快速测试爬虫"""
import sys
sys.path.insert(0, '.')
from scraper import run_all_scrapers

print("开始抓取...")
results = run_all_scrapers()
print(f"\n总计: {len(results)} 条")
for r in results[:10]:
    print(f"  [{r['source']}] {r['title'][:70]}")
