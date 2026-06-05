# Live Translator — 即時英中字幕翻譯工具

在開英文會議或看 YouTube 時，以懸浮視窗即時顯示英文原文 + 繁體中文翻譯。
完全本地離線，不傳任何資料到外部伺服器。

## 系統需求

- macOS 12 Ventura 以上
- Python 3.10+
- Apple Silicon（M1/M2/M3）或 Intel Mac

## 安裝步驟

### 第一步：安裝 BlackHole（只需做一次）

1. 到 https://existential.audio/blackhole/ 下載並安裝 **BlackHole 2ch**
2. 重新開機（或登出再登入）
3. 開啟「應用程式 → 工具程式 → 音訊 MIDI 設定」
4. 點左下角 `+` → 「建立多輸出裝置」
5. 勾選「BlackHole 2ch」和「MacBook Pro 喇叭」（或你的喇叭裝置）
6. 開啟「系統設定 → 聲音 → 輸出」，選擇剛建立的「多輸出裝置」

> 完成後你的喇叭照常播放，同時 BlackHole 也會接收到音訊供程式使用。

### 第二步：安裝 Python 套件

```bash
cd tools/live-translator
pip install -r requirements.txt
```

### 第三步：啟動程式

兩種方式擇一：

**方式 A — 雙擊桌面 App（最簡單）**

直接雙擊桌面的 `即時翻譯.app`。

> ⚠️ App 內的啟動腳本（`Contents/MacOS/LiveTranslator`）把本資料夾路徑寫死了。
> 若日後把專案資料夾搬家或改名，需同步修改該腳本裡的 `TOOL_DIR`，否則 App 會啟動失敗。

**方式 B — 終端機啟動**

```bash
cd tools/live-translator
source venv/bin/activate
python main.py
```

首次啟動會自動下載模型（約 600MB），請耐心等待。

## 使用方式

1. 啟動後選單列右上角出現 🎙 圖示
2. 點圖示 → 「開始翻譯」→ 圖示變為 🔴
3. 播放任何英文聲音（YouTube、Zoom、Teams）
4. 懸浮字幕視窗自動出現，即時顯示英文 + 中文翻譯
5. 不需要時點「暫停翻譯」或「結束」

## 字幕視窗操作

- **拖曳**：按住標題列拖曳到任意位置
- **清空字幕**：點選單列 → 清空字幕

## 常見問題

**Q：聽不到聲音 / 沒有字幕出現？**
確認系統音效輸出是「多輸出裝置」，不是直接選 BlackHole。

**Q：翻譯延遲很久？**
正常現象。首次辨識需要載入模型（約 10 秒），之後每句話延遲約 1-3 秒。

**Q：程式說找不到 BlackHole？**
重新確認第一步的設定，並確保系統輸出是「多輸出裝置」。
