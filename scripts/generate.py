"""每日市場新聞自動產生器"""
import feedparser
import os
import requests
from datetime import datetime, timezone, timedelta
from html import escape

TW_TZ = timezone(timedelta(hours=8))

FEEDS = {
    "美股 / 國際財經": [
        ("CNBC 財經", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069"),
        ("Yahoo 財經", "https://finance.yahoo.com/news/rssindex"),
        ("MarketWatch 頭條", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
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
html, body { background: #0a0a0a; }
body {
  color: #e8e8e8;
  font-family: 'Noto Sans TC', -apple-system, sans-serif;
  line-height: 1.7;
  padding: 2rem 1rem;
  min-height: 100vh;
  background-image:
    linear-gradient(rgba(0, 255, 170, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 255, 170, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
}
.container { max-width: 880px; margin: 0 auto; position: relative; }
.container::before {
  content: '';
  position: absolute;
  top: -10px; left: -10px;
  width: 40px; height: 40px;
  border-top: 2px solid #00ffaa;
  border-left: 2px solid #00ffaa;
}
.container::after {
  content: '';
  position: absolute;
  bottom: -10px; right: -10px;
  width: 40px; height: 40px;
  border-bottom: 2px solid #00ffaa;
  border-right: 2px solid #00ffaa;
}
header {
  border-bottom: 1px solid #222;
  padding-bottom: 1.5rem;
  margin-bottom: 2.5rem;
  position: relative;
}
header::after {
  content: '';
  position: absolute;
  bottom: -1px; left: 0;
  width: 80px; height: 1px;
  background: #00ffaa;
  box-shadow: 0 0 8px #00ffaa;
}
.meta {
  display: flex;
  justify-content: space-between;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 0.7rem;
  color: #00ffaa;
  letter-spacing: 0.3em;
  margin-bottom: 1.2rem;
  text-transform: uppercase;
}
.meta .blink { animation: blink 1.5s infinite; }
@keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0.2; } }
h1 {
  font-family: 'Noto Serif TC', serif;
  font-size: clamp(2.2rem, 6vw, 3.8rem);
  font-weight: 900;
  line-height: 1.1;
  letter-spacing: 0.05em;
  color: #ffffff;
  text-shadow: 0 0 30px rgba(0, 255, 170, 0.15);
}
h1 em {
  font-style: normal;
  background: linear-gradient(135deg, #00ffaa 0%, #00d4ff 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.tagline {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  color: #888;
  margin-top: 1rem;
  letter-spacing: 0.1em;
}
.tagline::before { content: '> '; color: #00ffaa; }
.section { margin-bottom: 3rem; }
.section h2 {
  font-family: 'Noto Serif TC', serif;
  font-size: 1.3rem;
  font-weight: 900;
  margin-bottom: 1.2rem;
  padding: 0.6rem 1rem;
  letter-spacing: 0.1em;
  color: #00ffaa;
  background: linear-gradient(90deg, rgba(0, 255, 170, 0.08) 0%, transparent 100%);
  border-left: 3px solid #00ffaa;
  position: relative;
}
.section h2::before {
  content: '[ ';
  font-family: 'JetBrains Mono', monospace;
  color: #00ffaa;
  opacity: 0.5;
}
.section h2::after {
  content: ' ]';
  font-family: 'JetBrains Mono', monospace;
  color: #00ffaa;
  opacity: 0.5;
}
.news-item {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 1.2rem;
  padding: 1rem 0.8rem;
  border-bottom: 1px solid #1a1a1a;
  transition: all 0.2s ease;
}
.news-item:hover {
  background: rgba(0, 255, 170, 0.04);
  border-bottom-color: #00ffaa;
}
.num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1rem;
  font-weight: 500;
  color: #00ffaa;
  opacity: 0.6;
  letter-spacing: 0.05em;
}
.news-body a {
  display: block;
  color: #e8e8e8;
  text-decoration: none;
  font-weight: 500;
  font-size: 1rem;
  line-height: 1.55;
  transition: color 0.2s;
}
.news-body a:hover { color: #00ffaa; }
.source {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #555;
  letter-spacing: 0.15em;
  margin-top: 0.5rem;
  display: inline-block;
  text-transform: uppercase;
}
footer {
  margin-top: 4rem;
  padding-top: 1.5rem;
  border-top: 1px solid #222;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #555;
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
  letter-spacing: 0.1em;
}
footer .status {
  color: #00ffaa;
}
footer .status::before {
  content: '● ';
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
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
        '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600;900&family=Noto+Sans+TC:wght@400;500&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">'
        '<style>' + CSS + '</style></head><body><div class="container">'
        '<header><div class="meta"><span class="blink">● MARKET BRIEF</span><span>' + now_str + '</span></div>'
        '<h1>晨間 <em>市場</em> 摘要</h1>'
        '<p class="tagline">昨夜美股 · 今晨台灣要聞 · 每日自動更新</p></header>'
        + body +
        '<footer><span class="status">SYSTEM ONLINE</span><span>LAST UPDATE ' + now_str + '</span></footer>'
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
    lines.append("—— 每日自動彙整 ——")

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
