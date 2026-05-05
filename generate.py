"""
每日市場新聞自動產生器
- 抓取美股、台灣財經、台灣綜合新聞 RSS
- 產生靜態 HTML 網頁
- 推播摘要到 Telegram
"""
import feedparser
import os
import requests
from datetime import datetime, timezone, timedelta
from html import escape

# 台灣時區
TW_TZ = timezone(timedelta(hours=8))

# RSS 來源(全部免費公開)
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

MAX_PER_FEED = 5  # 每個來源取幾條
MAX_PER_SECTION = 10  # 每個分類最多顯示幾條


def fetch_section(feed_list):
    """抓取一個分類下所有來源的最新新聞"""
    items = []
    for source_name, url in feed_list:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:MAX_PER_FEED]:
                items.append({
                    "title": entry.get("title", "(無標題)"),
                    "link": entry.get("link", "#"),
                    "source": source_name,
                    "published": entry.get("published", ""),
                    "published_parsed": entry.get("published_parsed"),
                })
        except Exception as e:
            print(f"  ⚠ {source_name} 抓取失敗: {e}")
    # 依時間排序,新的在前
    items.sort(
        key=lambda x: x["published_parsed"] or 0,
        reverse=True,
    )
    return items[:MAX_PER_SECTION]


def build_html(sections, now_str):
    """產生編輯部風格的靜態 HTML"""
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
<title>晨間市場摘要 · Daily Market Brief</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Noto+Serif+TC:wght@400;600;700&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #f4f1ea;
    color: #1a1a1a;
    font-family: 'Noto Serif TC', Georgia, serif;
    line-height: 1.6;
    padding: 2rem 1rem;
  }}
  .container {{ max-width: 880px; margin: 0 auto; }}
  header {{
    border-bottom: 4px double #1a1a1a;
    padding-bottom: 1rem;
    margin-bottom: 2rem;
  }}
  .meta {{
    display: flex;
    justify-content: space-between;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #5a5040;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-bottom: 1rem;
  }}
  h1 {{
    font-family: 'Playfair Display', 'Noto Serif TC', serif;
    font-size: clamp(2.5rem, 6vw, 4.5rem);
    font-weight: 900;
    line-height: 0.95;
    letter-spacing: -0.02em;
  }}
  h1 em {{ font-style: italic; color: #8b2635; }}
  .tagline {{
    font-size: 0.9rem;
    color: #5a5040;
    margin-top: 0.75rem;
  }}
  .section {{ margin-bottom: 2.5rem; }}
  .section h2 {{
    font-family: 'Playfair Display', 'Noto Serif TC', serif;
    font-size: 1.6rem;
    font-weight: 900;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #c4b8a0;
  }}
  .news-item {{
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 1rem;
    padding: 0.85rem 0;
    border-bottom: 1px solid #d4cab3;
    align-items: baseline;
  }}
  .num {{
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    font-weight: 900;
    font-style: italic;
    color: #c4b8a0;
    line-height: 1;
  }}
  .news-body a {{
    display: block;
    color: #1a1a1a;
    text-decoration: none;
    font-weight: 600;
    font-size: 1.05rem;
    line-height: 1.45;
    transition: color 0.2s;
  }}
  .news-body a:hover {{ color: #8b2635; }}
  .source {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #5a5040;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 0.3rem;
    display: inline-block;
  }}
  footer {{
    margin-top: 3rem;
    padding-top: 1rem;
    border-top: 2px solid #1a1a1a;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #5a5040;
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.5rem;
  }}
  @media (max-width: 600px) {{
    body {{ padding: 1rem 0.75rem; }}
    .news-body a {{ font-size: 0.95rem; }}
  }}
</style>
</head>
<body>
  <div class="container">
    <header>
      <div class="meta">
        <span>市場日報 · Market Brief</span>
        <span>{now_str}</span>
      </div>
      <h1>晨間 <em>市場</em> 摘要</h1>
      <p class="tagline">昨夜美股 · 今晨台灣要聞 · 每日自動更新</p>
    </header>
    {section_html}
    <footer>
      <span>由 GitHub Actions 自動彙整 · 資料僅供參考</span>
      <span>更新時間 {now_str}</span>
    </footer>
  </div>
</body>
</html>"""


def send_telegram(sections, now_str):
    """推播摘要到 Telegram"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("⚠ 未設定 Telegram 環境變數,跳過推播")
        return

    lines = [f"📰 *晨間市場摘要*", f"_{now_str}_", ""]
    for section_name, items in sections.items():
        if not items:
            continue
        lines.append(f"*— {section_name} —*")
        for item in items[:5]:  # Telegram 每分類取前 5 條
            title = item['title'][:80]
            lines.append(f"• [{title}]({item['link']})")
        lines.append("")

    text = "\n".join(lines)
    if len(text) > 4000:  # Telegram 長度限制
        text = text[:3950] + "\n\n_...更多請看網頁_"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }, timeout=15)
        if r.ok:
            print("✓ Telegram 推播成功")
        else:
            print(f"✗ Telegram 推播失敗: {r.text}")
    except Exception as e:
        print(f"✗ Telegram 推播錯誤: {e}")


def main():
    now = datetime.now(TW_TZ)
    now_str = now.strftime("%Y-%m-%d %H:%M")

    print(f"=== 開始彙整 {now_str} ===")
    sections = {}
    for section_name, feed_list in FEEDS.items():
        print(f"抓取分類:{section_name}")
        sections[section_name] = fetch_section(feed_list)
        print(f"  → {len(sections[section_name])} 條")

    # 產生網頁
    html = build_html(sections, now_str)
    os.makedirs("public", exist_ok=True)
    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✓ 已產生 public/index.html")

    # Telegram 推播
    send_telegram(sections, now_str)
    print("=== 完成 ===")


if __name__ == "__main__":
    main()
