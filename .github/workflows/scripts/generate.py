"""
每日市場新聞自動產生器
"""
import feedparser
import os
import requests
from datetime import datetime, timezone, timedelta
from html import escape

TW_TZ = timezone(timedelta(hours=8))

FEEDS = {
    "美股 / 國際財經": [
        ("CNBC Markets", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069"),
        ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
        ("MarketWatch Top", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ],
    "台灣財經": [
        ("經濟日報", "https://money.udn.com/rssfeed/news/1001/5589/5590?ch=money"),
        ("中央社財經", "https://feeds.feedburner.com/rsscna/finance"),
    ],
    "台灣要聞": [
        ("中央社政治", "https://feeds.feedburner.com/rsscna/politics"),
        ("中央社社會", "https://feeds.feedburner.com/rsscna/social"),
        ("中央社國際", "https://feeds.feedburner.com/rsscna/intworld"),
    ],
}

MAX_PER_FEED = 5
MAX_PER_SECTION = 10


def fetch_section(feed_list):
    items = []
    for source_name, url in feed_list:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:MAX_PER_FEED]:
                items.append({
                    "title": entry.get("title", "(無標題)"),
                    "link": entry.get("link", "#"),
                    "source": source_name,
                    "published_parsed": entry.get("published_parsed"),
                })
        except Exception as e:
            print(f"  WARN {source_name} failed: {e}")
    items.sort(key=lambda x: x["published_parsed"] or 0, reverse=True)
    return items[:MAX_PER_SECTION]


def build_html(sections, now_str):
    section_html = ""
    for section_name, items in sections.items():
        cards = ""
        for i, item in enumerate(items, 1):
            cards += f"""
            <article class="news-item">
              <span class="num">{i:02d}</span>
              <div class="news-body">
                <a href="{escape(item['link'])}" target="_blank" rel="noopener">{escape(item['title'])}</a>
                <span class="source">{escape(item['source'])}</span>
              </div>
            </article>
            """
        section_html += f"""
        <section class="section">
          <h2>{escape(section_name)}</h2>
          <div class="news-list">{cards}</div>
        </section>
        """

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>晨間市場摘要</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Noto+Serif+TC:wght@400;600;700&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #f4f1ea; color: #1a1a1a; font-family: 'Noto Serif TC', Georgia, serif; line-height: 1.6; padding: 2rem 1rem; }}
  .container {{ max-width: 880px; margin: 0 auto; }}
  header {{ border-bottom: 4px double #1a1a1a; padding-bottom: 1rem; margin-bottom: 2rem; }}
  .meta {{ display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #5a5040; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 1rem; }}
  h1 {{ font-family: 'Playfair Display', 'Noto Serif TC', serif; font-size: clamp(2.5rem, 6vw, 4.5rem); font-weight: 900; line-height: 0.95; letter-spacing: -0.02em; }}
  h1 em {{ font-style: italic; color: #8b2635; }}
  .tagline {{ font-size: 0.9rem; color: #5a5040; margin-top: 0.75rem; }}
  .section {{ margin-bottom: 2.5rem; }}
  .section h2 {{ font-family: 'Playfair Display', 'Noto Serif TC', serif; font-size: 1.6rem; font-weight: 900; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #c4b8a0; }}
  .news-item {{ display: grid; grid-template-columns: auto 1fr; gap: 1rem; padding: 0.85rem 0; border-bottom: 1px solid #d4cab3; align-items: baseline; }}
  .num​​​​​​​​​​​​​​​​
