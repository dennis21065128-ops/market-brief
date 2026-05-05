"""每日市場新聞自動產生器"""
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


def fetch_section(feed_list):
    items = []
    for source_name, url in feed_list:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:5]:
                items.append({
                    "title": entry.get("title", "(無標題)"),
                    "link": entry.get("link", "#"),
                    "source": source_name,
                    "pp": entry.get("published_parsed"),
                })
        except Exception as e:
            print("WARN", source_name, e)
    items.sort(key=lambda x: x["pp"] or 0, reverse=True)
    return items[:10]


CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #f4f1ea; color: #1a1a1a; font-family: 'Noto Serif TC', Georgia, serif; line-height: 1.6; padding: 2rem 1rem; }
.container { max-width: 880px; margin: 0 auto; }
header { border-bottom: 4px double #1a1a1a; padding-bottom: 1rem; margin-bottom: 2rem; }
.meta { display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #5a5040; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 1rem; }
h1 { font-family: 'Playfair Display', 'Noto Serif TC', serif; font-size: clamp(2.5rem, 6vw, 4.5rem); font-weight: 900; line-height: 0.95; letter-spacing: -0.02em; }
h1 em { font-style: italic; color: #8b2635; }
.tagline { font-size: 0.9rem; color: #5a5040; margin-top: 0.75rem; }
.section { margin-bottom: 2.5rem; }
.section h2 { font-family: 'Playfair Display', 'Noto Serif TC', serif; font-size: 1.6rem; font-weight: 900; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #c4b8a0; }
.news-item { display: grid; grid-template-columns: auto 1fr; gap: 1rem; padding: 0.85rem 0; border-bottom: 1px solid #d4cab3; }
.num { font-family: 'Playfair Display', serif; font-size: 1.5rem; font-weight: 900; font-style: italic; color: #c4b8a0; }
.news-body a { display: block; color: #1a1a1a; text-decoration: none; font-weight: 600; font-size: 1.05rem; line-height: 1.45; }
.news-body a:hover { color: #8b2635; }
.source { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #5a5040; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 0.3rem; display: inline-block; }
footer { margin-top: 3rem; padding-top: 1rem; border-top: 2px solid #1a1a1a; font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #5a5040; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; }
"""


def build_html(sections, now_str):
    parts = []
    for name, items in sections.items():
        cards = ""
        for i, it in enumerate(items, 1):
            cards += '<article class="news-item"><span class="num">{:02d}</span><div class="news-body"><a href="{}" target="_blank" rel="noopener">{}</a><span class="source">{}</span></div></article>'.format(
                i, escape(it["link"]), escape(it["title"]), escape(it["source"])
            )
        parts.append('<section class="section"><h2>{}</h2>{}</section>'.format(escape(name), cards))

    body = "".join(parts)
    html = (
        '<!DOCTYPE html><html lang="zh-TW"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        '<title>晨間市場摘要</title>'
        '<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Noto+Serif+TC:wght@400;600;700&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">'
        '<style>' + CSS + '</style></head><body><div class="container">'
        '<header><div class="meta"><span>市場日報 · Market Brief</span><span>' + now_str + '</span></div>'
        '<h1>晨間 <em>市場</em> 摘要</h1>'
        '<p class="tagline">昨夜美股 · 今晨台灣要聞 · 每日自動更新</p></header>'
        + body +
        '<footer><span>由 GitHub Actions 自動彙整 · 資料僅供參考</span><span>更新時間 ' + now_str + '</span></footer>'
        '</div></body></html>'
    )
    return html


def send_telegram(sections, now_str):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("WARN no telegram env")
        return

    lines = ["📰 *晨間市場摘要*", "_" + now_str + "_", ""]
    for name, items in sections.items():
        if not items:
            continue
        lines.append("*— " + name + " —*")
        for it in items[:5]:
            t = it["title"][:80].replace("[", "(").replace("]", ")")
            lines.append("• [" + t + "](" + it["link"] + ")")
        lines.append("")

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:3950] + "\n\n_...更多請看網頁_"

    url = "https://api.telegram.org/bot" + token + "/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }, timeout=15)
        if r.ok:
            print("OK telegram sent")
        else:
            print("FAIL telegram:", r.text)
    except Exception as e:
        print("FAIL telegram err:", e)


def main():
    now = datetime.now(TW_TZ).strftime("%Y-%m-%d %H:%M")
    print("===", now, "===")
    sections = {}
    for name, feeds in FEEDS.items():
        print("Fetch:", name)
        sections[name] = fetch_section(feeds)
        print("  ->", len(sections[name]))

    html = build_html(sections, now)
    os.makedirs("public", exist_ok=True)
    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("OK index.html")

    send_telegram(sections, now)
    print("=== done ===")


if __name__ == "__main__":
    main()
