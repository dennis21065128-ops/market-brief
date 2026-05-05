# 晨間市場摘要 · 自動部署指南

每天早上 7:00 自動抓取美股、台灣財經、台灣要聞,更新到 GitHub Pages 並推播到 Telegram。

---

## 一次性設定(約 15 分鐘)

### 步驟 1:建立 Telegram Bot(2 分鐘)

1. 在 Telegram 搜尋 `@BotFather`,開始對話
2. 傳送 `/newbot`,跟著提示取個名字(例如 `my_market_brief_bot`)
3. BotFather 會給你一串 token,長這樣:`123456789:ABCdef...`,**先記下**
4. 在 Telegram 搜尋你剛建立的 bot,按「Start」開始對話,隨便傳一句話
5. 在瀏覽器打開:
   ```
   https://api.telegram.org/bot<你的TOKEN>/getUpdates
   ```
   找到 `"chat":{"id":xxxxxxxx}`,**那串數字就是你的 chat id**

### 步驟 2:建立 GitHub Repo(3 分鐘)

1. 登入 GitHub,點右上角 `+` → `New repository`
2. 名字填 `market-brief`(或你喜歡的),設為 **Public**
3. 建立後,把這個資料夾裡的所有檔案上傳上去
   - 直接拖拉:點 `uploading an existing file` → 拖入所有檔案和資料夾
   - 或用 git:
     ```
     git clone https://github.com/你的帳號/market-brief.git
     # 把檔案複製進去
     git add . && git commit -m "init" && git push
     ```

### 步驟 3:設定 Secrets(2 分鐘)

在你的 repo 頁面:
1. `Settings` → `Secrets and variables` → `Actions` → `New repository secret`
2. 新增兩個:
   - Name: `TELEGRAM_BOT_TOKEN`,Value: 步驟 1 的 token
   - Name: `TELEGRAM_CHAT_ID`,Value: 步驟 1 的 chat id

### 步驟 4:啟用 GitHub Pages(1 分鐘)

1. `Settings` → `Pages`
2. Source 選 `Deploy from a branch`
3. Branch 選 `gh-pages`(第一次跑完後才會出現,可以先跳過,先做步驟 5)

### 步驟 5:首次手動觸發(1 分鐘)

1. 進入 repo 的 `Actions` 分頁
2. 左側點 `Daily Market Brief`
3. 右上角點 `Run workflow` → `Run workflow`
4. 等 1-2 分鐘跑完
5. 跑完後回步驟 4 設定 Pages,選 `gh-pages` branch

完成後,你的網站網址會是:
```
https://你的帳號.github.io/market-brief/
```

每天早上 7:00 會自動更新網頁,並把摘要推到你的 Telegram。

---

## 想客製化?

- **改推播時間**:編輯 `.github/workflows/daily.yml` 裡的 cron 設定。注意 GitHub 用 UTC 時間,台灣時間 7:00 = UTC 23:00(前一天)
- **加減新聞來源**:編輯 `scripts/generate.py` 上方的 `FEEDS` 字典
- **每日跑兩次**:在 cron 加一行,例如早晚各一次:
  ```yaml
  - cron: '0 23 * * *'   # 早上 7:00
  - cron: '0 11 * * *'   # 晚上 7:00
  ```

## 疑難排解

- **Action 失敗**:點進失敗的 run 看錯誤訊息,通常是 RSS 來源暫時掛掉,隔天就會恢復
- **沒收到 Telegram**:確認你有先跟 bot 傳過訊息(否則 bot 不能主動傳給你)
- **網頁 404**:確認 GitHub Pages 設定的 branch 是 `gh-pages`
