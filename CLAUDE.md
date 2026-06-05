# claude-2026-project — 我的班級工具總專案

## 對話開始時請先讀
進度與最近更動都在 Obsidian：`secondbrain/claude-2026-project/工作筆記.md`

## 工作模式
- **加新工具**：對 Claude 說「我想做一個 XXX 工具」→ Claude 會建 `tools/<工具名>/` 子資料夾、引導我跟著影片做
- **結束工作**：對 Claude 說「**收工**」→ 自動 commit + push + 更新 Obsidian 工作筆記
- **接續工作**：對 Claude 說「讀工作筆記、告訴我上次做到哪」

## 工作桌 + 三個家
- 📋 GDrive 工作桌：`~/Library/CloudStorage/GoogleDrive-heero7394@gmail.com/我的雲端硬碟/個人系統/claude-2026-project/`（自動跨電腦同步）
- 🐙 GitHub repo：`Henrychou1984/claude-2026-project`（公開，網頁的家）
- 📘 Obsidian 駕駛艙：`secondbrain/claude-2026-project/工作筆記.md`（想法的家）
- 🔥 Firebase 專案：`my-teaching-tools`（資料的家）

## 工具清單
（之後加新工具時會自動更新）
- **live-translator** (`tools/live-translator/`)：macOS 即時英中字幕翻譯，系統音訊 → faster-whisper → Argos Translate → 懸浮視窗。啟動方式二選一：①雙擊桌面的 `即時翻譯.app`（內含啟動腳本，路徑寫死指向本資料夾，搬家後需同步更新）②終端機 `source venv/bin/activate && python main.py`

## 開工 / 收工 SOP
完整流程已收斂到**全域技能**（`~/.claude/skills/start-work`、`end-work`），所有專案共用、單一維護來源。
- 說「**開工**」→ 讀工作筆記摘要進度 + `git status`/`fetch` + 建議下一步
- 說「**收工**」→ 摘要今天 + 更新工作筆記 + `git add/commit/push` + 三勾表格
- 本專案的工作筆記固定在：`~/Library/CloudStorage/GoogleDrive-heero7394@gmail.com/我的雲端硬碟/個人系統/secondbrain/claude-2026-project/工作筆記.md`

## 工作注意事項
- 學生資料一律去識別化（只用座號 + 班級代號）
- commit 訊息要寫清楚做了什麼 + 為什麼
- 收工前說「收工」讓 Claude 同步三方
