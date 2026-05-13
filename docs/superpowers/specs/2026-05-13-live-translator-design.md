# Live Translator — 即時英中字幕翻譯工具 設計規格

**日期**：2026-05-13
**工具路徑**：`tools/live-translator/`
**狀態**：已核准，待實作

---

## 一、目標

在開英文會議（Zoom、Teams）或觀看 YouTube 英文內容時，以懸浮視窗即時顯示英文原文＋繁體中文翻譯字幕，幫助使用者即時理解。

---

## 二、使用情境

- 使用者在 Mac 上播放英文內容（YouTube、線上會議）
- 開啟選單列圖示 → 點「開始翻譯」
- 懸浮字幕視窗出現在螢幕任意角落（可拖曳）
- 視窗即時顯示：灰色草稿英文（辨識中）→ 白色鎖定英文（辨識完成）→ 藍色繁中翻譯
- 不需要時點選單列「暫停」或「結束」

---

## 三、技術選型

| 元件 | 套件 | 說明 |
|------|------|------|
| 系統音訊抓取 | BlackHole 2ch（前置安裝）+ sounddevice | 擷取 Mac 系統播放的所有聲音 |
| 語音活動偵測 | Silero VAD（via faster-whisper 內建） | 偵測說話片段，避免翻譯靜音 |
| 語音辨識 | faster-whisper（small 模型） | 本地離線，Apple Silicon 加速，串流輸出 |
| 翻譯引擎 | Argos Translate（en→zh 模型） | 完全離線，模型約 100MB |
| 選單列 | rumps | macOS 選單列圖示常駐 |
| 懸浮視窗 | tkinter | 可拖曳、Always on Top、半透明背景 |

**Python 版本要求**：3.10+
**平台**：macOS only（因 BlackHole 和 rumps 限定）

---

## 四、架構與資料流

```
[系統音訊輸出]
    ↓ BlackHole 虛擬音效驅動（使用者一次性設定）
[sounddevice 抓取執行緒]  16kHz, mono, chunk=1秒
    ↓
[Silero VAD]  偵測說話起止點，切割語音片段
    ↓
[faster-whisper]  串流辨識，逐字輸出 interim → final
    ↓
[Argos Translate]  final 句子送翻譯，輸出繁中
    ↓
[tkinter UI 主執行緒]  更新顯示：EN 草稿 / EN 鎖定 / 中文
```

---

## 五、UI 規格

### 懸浮視窗
- **尺寸**：寬 340px，高自動（約 150-200px）
- **背景**：半透明深色（`rgba(15,23,42,0.88)`），毛玻璃效果
- **Always on Top**：`wm_attributes('-topmost', True)`
- **可拖曳**：綁定標題列 `<Button-1>` + `<B1-Motion>`
- **無外框**：`overrideredirect(True)` + 圓角外觀

### 內容區塊（上到下）
1. **標題列**：三點（關閉/最小化/最大化假按鈕）＋「即時翻譯」＋綠點「聆聽中」狀態
2. **英文欄**：標籤「EN」＋辨識文字（草稿灰 `#94a3b8` / 鎖定白 `#e2e8f0`）
3. **分隔線**
4. **中文欄**：標籤「中文」＋翻譯文字（藍 `#38bdf8`，字級比英文大 2px）
5. **底部工具列**：字體放大 / 縮小 / 透明度調整 / 清空

### 選單列
- 圖示：🎙（靜止）/ 🔴（錄音中）
- 選單項目：
  - 「開始翻譯」/ 「暫停翻譯」（切換）
  - 「清空字幕」
  - 分隔線
  - 「結束」

---

## 六、即時串流顯示邏輯

1. faster-whisper 在辨識過程中持續輸出 **interim**（未完成）文字
2. interim 文字顯示為灰色，末尾加閃爍游標 `|`
3. 辨識完成後輸出 **final** 文字，替換 interim，顯示為白色
4. final 文字送入 Argos Translate 翻譯
5. 翻譯結果顯示在中文欄（取代前一句）
6. 下一句 interim 出現時，英文欄顯示新草稿（舊 final 消失）

---

## 七、錯誤處理

| 情境 | 處理方式 |
|------|----------|
| BlackHole 未安裝 / 未設定 | 啟動時偵測音訊裝置，若找不到 BlackHole 則跳出提示視窗，附官網連結與設定說明 |
| faster-whisper 模型未下載 | 首次啟動自動下載，tkinter 視窗顯示進度條 |
| Argos 翻譯模型未下載 | 同上，自動下載 |
| 長時間靜音 / 噪音 | VAD 不觸發辨識，UI 顯示「— 等待聲音 —」 |
| 翻譯失敗（例外錯誤） | 保留英文原文，中文欄顯示「翻譯暫時失敗」，不中斷程式 |
| 音訊串流中斷 | 捕捉例外，自動嘗試重連，選單列顯示警告圖示 |

---

## 八、安裝流程（使用者視角）

1. 安裝 BlackHole 2ch（一次性）：到官網下載 pkg 安裝
2. 在「音訊 MIDI 設定」建立「多輸出裝置」（BlackHole + 內建喇叭）
3. 將系統輸出改為「多輸出裝置」
4. `pip install -r requirements.txt`（首次）
5. `python main.py` 啟動，首次自動下載模型（~600MB）
6. 點選單列圖示 → 開始翻譯

---

## 九、檔案結構

```
tools/live-translator/
├── main.py              # 進入點：初始化 rumps app + tkinter 視窗
├── audio.py             # 系統音訊抓取（sounddevice，偵測 BlackHole 裝置）
├── transcriber.py       # faster-whisper 串流辨識 + Silero VAD
├── translator.py        # Argos Translate 初始化 + 翻譯
├── ui.py                # tkinter 懸浮視窗（拖曳、透明、Always on Top）
├── requirements.txt     # 套件清單
└── README.md            # 安裝與使用說明
```

---

## 十、不在此版本範圍內

- 多語言支援（只做英→繁中）
- 歷史記錄儲存
- 字幕匯出
- Windows / Linux 支援
- 麥克風輸入模式
