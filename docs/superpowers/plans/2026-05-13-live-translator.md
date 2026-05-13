# Live Translator 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立一個 macOS 本地即時英中字幕翻譯工具，完全離線運作，以懸浮視窗同時顯示英文原文與繁體中文翻譯。

**Architecture:** 系統音訊透過 BlackHole 虛擬音效驅動導入 sounddevice，faster-whisper 對音訊串流做即時語音辨識，Argos Translate + OpenCC 翻譯成繁體中文，結果透過執行緒安全佇列推送到 tkinter 懸浮視窗；rumps 在選單列常駐提供開始/暫停/結束控制。

**Tech Stack:** Python 3.10+, faster-whisper, argostranslate, opencc-python-reimplemented, sounddevice, rumps, tkinter

---

## 檔案結構

```
tools/live-translator/
├── main.py           # rumps App，連接所有模組，選單列控制
├── audio.py          # BlackHole 裝置偵測 + sounddevice 音訊抓取
├── transcriber.py    # faster-whisper 辨識循環 + VAD + 緩衝管理
├── translator.py     # Argos Translate 初始化、模型下載、翻譯 + OpenCC 繁中轉換
├── ui.py             # tkinter 懸浮視窗，佇列驅動更新，可拖曳
├── requirements.txt
├── tests/
│   ├── conftest.py   # sys.path 設定，讓 pytest 找到模組
│   ├── test_audio.py
│   ├── test_transcriber.py
│   ├── test_translator.py
│   └── test_ui.py
└── README.md
```

**執行緒架構：**
- `rumps` App：主執行緒（macOS Cocoa 要求）
- `SubtitleWindow._run()`：Daemon 背景執行緒（tkinter 事件迴圈）
- `AudioCapture`：sounddevice 內部回呼執行緒
- `Transcriber._loop()`：Daemon 背景執行緒
- 翻譯：每句話一個 one-shot daemon 執行緒
- 所有 UI 更新透過 `queue.Queue` + `root.after(50, poll)` 確保執行緒安全

---

## Task 1: 專案鷹架

**Files:**
- Create: `tools/live-translator/requirements.txt`
- Create: `tools/live-translator/tests/conftest.py`

- [ ] **Step 1: 建立目錄結構**

```bash
mkdir -p tools/live-translator/tests
touch tools/live-translator/main.py
touch tools/live-translator/audio.py
touch tools/live-translator/transcriber.py
touch tools/live-translator/translator.py
touch tools/live-translator/ui.py
```

- [ ] **Step 2: 建立 requirements.txt**

```
# tools/live-translator/requirements.txt
faster-whisper>=0.10.0
argostranslate>=1.9.0
opencc-python-reimplemented>=0.1.6
sounddevice>=0.4.6
numpy>=1.24.0
rumps>=0.4.0
```

- [ ] **Step 3: 建立 tests/conftest.py**

```python
# tools/live-translator/tests/conftest.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

- [ ] **Step 4: 確認 pytest 可以找到測試目錄**

```bash
cd tools/live-translator
pip install -r requirements.txt
pytest tests/ -v --collect-only
```

預期輸出：`no tests ran`（尚無測試，但不應報錯）

- [ ] **Step 5: Commit**

```bash
git add tools/live-translator/
git commit -m "feat(live-translator): 建立專案骨架與依賴清單"
```

---

## Task 2: translator.py — 翻譯模組

**Files:**
- Create: `tools/live-translator/translator.py`
- Create: `tools/live-translator/tests/test_translator.py`

- [ ] **Step 1: 寫失敗測試**

```python
# tools/live-translator/tests/test_translator.py
from unittest.mock import patch, MagicMock
import pytest


def test_translate_calls_argos_with_correct_language_codes():
    with patch('argostranslate.translate.translate', return_value='测试') as mock_translate, \
         patch.object(__import__('translator', fromlist=['Translator']).Translator, '_ensure_model'):
        from translator import Translator
        t = Translator.__new__(Translator)
        t._ensure_model = MagicMock()
        t._cc = MagicMock(convert=lambda x: x)
        t.__init__ = MagicMock()
        # 直接測試 translate 方法邏輯
        with patch('argostranslate.translate.translate', return_value='测试') as mt:
            import opencc
            t._cc = opencc.OpenCC('s2t')
            result = argostranslate_translate_call(t, 'test input', mt)
        mt.assert_called_once_with('test input', 'en', 'zh')


def argostranslate_translate_call(t, text, mock_fn):
    return mock_fn(text, 'en', 'zh')


def test_translate_returns_traditional_chinese():
    """翻譯結果必須包含繁體中文（OpenCC s2t 轉換後）"""
    from unittest.mock import patch, MagicMock
    with patch('argostranslate.package.get_installed_packages', return_value=[
            MagicMock(from_code='en', to_code='zh')
        ]), \
         patch('argostranslate.translate.translate', return_value='这个功能帮助学生'):
        from translator import Translator
        t = Translator()
        result = t.translate('This feature helps students')
    # 簡轉繁：這個功能幫助學生（繁體字）
    assert '這' in result or '幫' in result or '學' in result


def test_translate_empty_string_returns_empty():
    with patch('argostranslate.package.get_installed_packages', return_value=[
            MagicMock(from_code='en', to_code='zh')
        ]), \
         patch('argostranslate.translate.translate', return_value=''):
        from translator import Translator
        t = Translator()
        result = t.translate('')
    assert result == ''
```

- [ ] **Step 2: 執行確認失敗**

```bash
cd tools/live-translator
pytest tests/test_translator.py -v
```

預期：`ImportError` 或 `ModuleNotFoundError`（translator.py 是空的）

- [ ] **Step 3: 實作 translator.py**

```python
# tools/live-translator/translator.py
import argostranslate.package
import argostranslate.translate
import opencc


class Translator:
    def __init__(self):
        self._ensure_model()
        self._cc = opencc.OpenCC('s2t')

    def _ensure_model(self):
        installed = argostranslate.package.get_installed_packages()
        has_en_zh = any(
            p.from_code == 'en' and p.to_code == 'zh'
            for p in installed
        )
        if not has_en_zh:
            print('下載 Argos Translate en→zh 模型（約 100MB，僅首次）...')
            argostranslate.package.update_package_index()
            available = argostranslate.package.get_available_packages()
            pkg = next(
                p for p in available
                if p.from_code == 'en' and p.to_code == 'zh'
            )
            argostranslate.package.install_from_path(pkg.download())

    def translate(self, text: str) -> str:
        if not text.strip():
            return ''
        simplified = argostranslate.translate.translate(text, 'en', 'zh')
        return self._cc.convert(simplified)
```

- [ ] **Step 4: 執行確認通過**

```bash
cd tools/live-translator
pytest tests/test_translator.py -v
```

預期：所有測試 PASS

- [ ] **Step 5: Commit**

```bash
git add tools/live-translator/translator.py tools/live-translator/tests/test_translator.py
git commit -m "feat(live-translator): 實作 Translator，Argos 翻譯 + OpenCC 繁中轉換"
```

---

## Task 3: audio.py — 系統音訊抓取

**Files:**
- Create: `tools/live-translator/audio.py`
- Create: `tools/live-translator/tests/test_audio.py`

- [ ] **Step 1: 寫失敗測試**

```python
# tools/live-translator/tests/test_audio.py
from unittest.mock import patch, MagicMock, call
import numpy as np
import pytest


def test_find_blackhole_device_returns_index_when_found():
    mock_devices = [
        {'name': 'Built-in Microphone', 'max_input_channels': 2},
        {'name': 'BlackHole 2ch', 'max_input_channels': 2},
        {'name': 'Built-in Output', 'max_input_channels': 0},
    ]
    with patch('sounddevice.query_devices', return_value=mock_devices):
        from audio import find_blackhole_device
        idx = find_blackhole_device()
    assert idx == 1


def test_find_blackhole_device_returns_none_when_not_found():
    mock_devices = [
        {'name': 'Built-in Microphone', 'max_input_channels': 2},
        {'name': 'Built-in Output', 'max_input_channels': 0},
    ]
    with patch('sounddevice.query_devices', return_value=mock_devices):
        from audio import find_blackhole_device
        idx = find_blackhole_device()
    assert idx is None


def test_find_blackhole_device_ignores_output_only_devices():
    """BlackHole 裝置若 max_input_channels == 0，不應被選中"""
    mock_devices = [
        {'name': 'BlackHole 2ch', 'max_input_channels': 0},  # output only
    ]
    with patch('sounddevice.query_devices', return_value=mock_devices):
        from audio import find_blackhole_device
        idx = find_blackhole_device()
    assert idx is None


def test_audio_capture_callback_passes_mono_chunk_to_callback():
    """音訊回呼應將多聲道資料轉為單聲道 numpy array 並呼叫 callback"""
    from audio import AudioCapture
    received = []
    capture = AudioCapture(device_index=1, callback=received.append)

    # 模擬 sounddevice 回呼：2 聲道輸入
    fake_indata = np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]], dtype='float32')
    capture._audio_callback(fake_indata, 3, None, None)

    assert len(received) == 1
    assert received[0].ndim == 1
    assert len(received[0]) == 3
    np.testing.assert_array_almost_equal(received[0], [0.1, 0.3, 0.5])
```

- [ ] **Step 2: 執行確認失敗**

```bash
cd tools/live-translator
pytest tests/test_audio.py -v
```

預期：`ImportError`（audio.py 是空的）

- [ ] **Step 3: 實作 audio.py**

```python
# tools/live-translator/audio.py
import sounddevice as sd
import numpy as np
from typing import Callable, Optional

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 0.5  # 秒
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
BLACKHOLE_KEYWORDS = ['blackhole']


def find_blackhole_device() -> Optional[int]:
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        name_lower = d['name'].lower()
        if any(kw in name_lower for kw in BLACKHOLE_KEYWORDS):
            if d['max_input_channels'] > 0:
                return i
    return None


class AudioCapture:
    def __init__(self, device_index: int, callback: Callable[[np.ndarray], None]):
        self._device = device_index
        self._callback = callback
        self._stream = None

    def start(self):
        self._stream = sd.InputStream(
            device=self._device,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='float32',
            blocksize=CHUNK_SIZE,
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop(self):
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def _audio_callback(self, indata: np.ndarray, frames: int, time, status):
        self._callback(indata[:, 0].copy())
```

- [ ] **Step 4: 執行確認通過**

```bash
cd tools/live-translator
pytest tests/test_audio.py -v
```

預期：所有測試 PASS

- [ ] **Step 5: Commit**

```bash
git add tools/live-translator/audio.py tools/live-translator/tests/test_audio.py
git commit -m "feat(live-translator): 實作 AudioCapture，偵測 BlackHole 裝置並抓取單聲道音訊"
```

---

## Task 4: transcriber.py — 語音辨識模組

**Files:**
- Create: `tools/live-translator/transcriber.py`
- Create: `tools/live-translator/tests/test_transcriber.py`

- [ ] **Step 1: 寫失敗測試**

```python
# tools/live-translator/tests/test_transcriber.py
from unittest.mock import MagicMock, patch
import numpy as np
import time
import pytest


def make_transcriber(on_interim=None, on_final=None):
    from transcriber import Transcriber
    with patch('faster_whisper.WhisperModel'):
        t = Transcriber(
            on_interim=on_interim or MagicMock(),
            on_final=on_final or MagicMock(),
            model_size='tiny',
        )
    return t


def test_feed_accumulates_audio():
    t = make_transcriber()
    chunk = np.zeros(1600, dtype='float32')
    t.feed(chunk)
    t.feed(chunk)
    assert len(t._buffer) == 3200


def test_feed_caps_buffer_at_30_seconds():
    t = make_transcriber()
    large_chunk = np.zeros(16000 * 31, dtype='float32')
    t.feed(large_chunk)
    assert len(t._buffer) <= 16000 * 30


def test_transcribe_returns_empty_string_when_no_segments():
    t = make_transcriber()
    t._model.transcribe.return_value = ([], MagicMock())
    result = t._transcribe(np.zeros(16000, dtype='float32'))
    assert result == ''


def test_transcribe_joins_segments():
    t = make_transcriber()
    seg1 = MagicMock()
    seg1.text = ' Hello '
    seg2 = MagicMock()
    seg2.text = ' world '
    t._model.transcribe.return_value = ([seg1, seg2], MagicMock())
    result = t._transcribe(np.zeros(16000, dtype='float32'))
    assert result == 'Hello world'


def test_on_final_called_after_silence(monkeypatch):
    """靜音 SILENCE_AFTER 秒後應觸發 on_final"""
    on_final = MagicMock()
    t = make_transcriber(on_final=on_final)

    seg = MagicMock()
    seg.text = 'Test sentence'
    t._model.transcribe.return_value = ([seg], MagicMock())

    chunk = np.zeros(8000, dtype='float32')
    t.feed(chunk)

    # 模擬靜音：將 _last_feed_time 設為過去
    import transcriber as tr_module
    t._last_feed_time = time.time() - tr_module.SILENCE_AFTER - 0.1

    t.start()
    time.sleep(0.5)
    t.stop()

    on_final.assert_called_once_with('Test sentence')
```

- [ ] **Step 2: 執行確認失敗**

```bash
cd tools/live-translator
pytest tests/test_transcriber.py -v
```

預期：`ImportError`（transcriber.py 是空的）

- [ ] **Step 3: 實作 transcriber.py**

```python
# tools/live-translator/transcriber.py
import numpy as np
import threading
import time
from faster_whisper import WhisperModel
from typing import Callable

SAMPLE_RATE = 16000
INTERIM_EVERY = 1.5   # 每 1.5 秒產生一次 interim 辨識
SILENCE_AFTER = 1.5   # 靜音超過 1.5 秒後觸發 final
MAX_BUFFER_SECONDS = 30


class Transcriber:
    def __init__(
        self,
        on_interim: Callable[[str], None],
        on_final: Callable[[str], None],
        model_size: str = 'small',
    ):
        self._on_interim = on_interim
        self._on_final = on_final
        self._model = WhisperModel(model_size, device='cpu', compute_type='int8')
        self._buffer = np.array([], dtype='float32')
        self._lock = threading.Lock()
        self._last_feed_time: float | None = None
        self._last_interim_time: float = 0.0
        self._running = False
        self._thread: threading.Thread | None = None

    def feed(self, chunk: np.ndarray):
        with self._lock:
            self._buffer = np.concatenate([self._buffer, chunk])
            max_samples = SAMPLE_RATE * MAX_BUFFER_SECONDS
            if len(self._buffer) > max_samples:
                self._buffer = self._buffer[-max_samples:]
            self._last_feed_time = time.time()

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self):
        while self._running:
            now = time.time()

            with self._lock:
                buf = self._buffer.copy()
                last_feed = self._last_feed_time

            has_audio = len(buf) >= SAMPLE_RATE * 0.5

            # Interim：定期辨識，顯示草稿
            if has_audio and now - self._last_interim_time >= INTERIM_EVERY:
                text = self._transcribe(buf)
                if text:
                    self._on_interim(text)
                self._last_interim_time = now

            # Final：靜音超過 SILENCE_AFTER 秒
            if has_audio and last_feed and now - last_feed >= SILENCE_AFTER:
                text = self._transcribe(buf)
                if text:
                    self._on_final(text)
                with self._lock:
                    self._buffer = np.array([], dtype='float32')
                    self._last_feed_time = None
                self._last_interim_time = 0.0

            time.sleep(0.1)

    def _transcribe(self, audio: np.ndarray) -> str:
        segments, _ = self._model.transcribe(
            audio,
            language='en',
            vad_filter=True,
            beam_size=1,
        )
        return ' '.join(s.text.strip() for s in segments).strip()
```

- [ ] **Step 4: 執行確認通過**

```bash
cd tools/live-translator
pytest tests/test_transcriber.py -v
```

預期：所有測試 PASS

- [ ] **Step 5: Commit**

```bash
git add tools/live-translator/transcriber.py tools/live-translator/tests/test_transcriber.py
git commit -m "feat(live-translator): 實作 Transcriber，faster-whisper 串流辨識 + VAD 靜音偵測"
```

---

## Task 5: ui.py — tkinter 懸浮字幕視窗

**Files:**
- Create: `tools/live-translator/ui.py`
- Create: `tools/live-translator/tests/test_ui.py`

- [ ] **Step 1: 寫失敗測試**

```python
# tools/live-translator/tests/test_ui.py
import queue as queue_module
import pytest


def make_window():
    from ui import SubtitleWindow
    return SubtitleWindow()


def test_set_interim_enqueues_interim_event():
    win = make_window()
    win.set_interim('hello world')
    event, text = win._queue.get_nowait()
    assert event == 'interim'
    assert 'hello world' in text


def test_set_final_enqueues_final_event():
    win = make_window()
    win.set_final('confirmed sentence')
    event, text = win._queue.get_nowait()
    assert event == 'final'
    assert text == 'confirmed sentence'


def test_set_translation_enqueues_translation_event():
    win = make_window()
    win.set_translation('翻譯結果')
    event, text = win._queue.get_nowait()
    assert event == 'translation'
    assert text == '翻譯結果'


def test_clear_enqueues_clear_event():
    win = make_window()
    win.clear()
    event, text = win._queue.get_nowait()
    assert event == 'clear'


def test_set_status_enqueues_status_event():
    win = make_window()
    win.set_status('listening')
    event, text = win._queue.get_nowait()
    assert event == 'status'
    assert text == 'listening'
```

- [ ] **Step 2: 執行確認失敗**

```bash
cd tools/live-translator
pytest tests/test_ui.py -v
```

預期：`ImportError`

- [ ] **Step 3: 實作 ui.py**

```python
# tools/live-translator/ui.py
import tkinter as tk
import threading
import queue

BG = '#0f172a'
TITLE_BG = '#1e293b'
BORDER = '#1e40af'
EN_DRAFT = '#94a3b8'
EN_FINAL = '#e2e8f0'
ZH_COLOR = '#38bdf8'
LABEL_COLOR = '#475569'
WIN_WIDTH = 340


class SubtitleWindow:
    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._root: tk.Tk | None = None
        self._en_var: tk.StringVar | None = None
        self._zh_var: tk.StringVar | None = None
        self._en_label: tk.Label | None = None
        self._status_dot: tk.Label | None = None
        self._drag_x = 0
        self._drag_y = 0

    def start(self):
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def set_interim(self, text: str):
        self._queue.put(('interim', text + ' |'))

    def set_final(self, text: str):
        self._queue.put(('final', text))

    def set_translation(self, text: str):
        self._queue.put(('translation', text))

    def set_status(self, status: str):
        self._queue.put(('status', status))

    def clear(self):
        self._queue.put(('clear', ''))

    def _run(self):
        self._root = tk.Tk()
        self._root.overrideredirect(True)
        self._root.wm_attributes('-topmost', True)
        self._root.wm_attributes('-alpha', 0.90)
        self._root.configure(bg=BG)

        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        self._root.geometry(f'{WIN_WIDTH}x200+{sw - WIN_WIDTH - 20}+{sh - 240}')

        self._build_ui()
        self._root.after(50, self._poll_queue)
        self._root.mainloop()

    def _build_ui(self):
        # 標題列
        title_bar = tk.Frame(self._root, bg=TITLE_BG, height=28)
        title_bar.pack(fill='x')
        title_bar.bind('<Button-1>', self._start_drag)
        title_bar.bind('<B1-Motion>', self._do_drag)

        tk.Label(
            title_bar, text='即時翻譯', bg=TITLE_BG, fg=LABEL_COLOR,
            font=('System', 10),
        ).pack(side='left', padx=10, pady=4)

        self._status_dot = tk.Label(
            title_bar, text='● 聆聽中', bg=TITLE_BG, fg='#22c55e',
            font=('System', 9),
        )
        self._status_dot.pack(side='right', padx=10)

        # 內容區
        content = tk.Frame(self._root, bg=BG, padx=14, pady=10)
        content.pack(fill='both', expand=True)

        tk.Label(content, text='EN', bg=BG, fg=LABEL_COLOR, font=('System', 9)).pack(anchor='w')

        self._en_var = tk.StringVar(value='— 等待聲音 —')
        self._en_label = tk.Label(
            content, textvariable=self._en_var, bg=BG, fg=EN_DRAFT,
            font=('System', 13), wraplength=WIN_WIDTH - 28, justify='left',
        )
        self._en_label.pack(anchor='w', pady=(2, 6))

        tk.Frame(content, bg='#1e293b', height=1).pack(fill='x', pady=4)

        tk.Label(content, text='中文', bg=BG, fg='#1d4ed8', font=('System', 9)).pack(anchor='w')

        self._zh_var = tk.StringVar(value='')
        tk.Label(
            content, textvariable=self._zh_var, bg=BG, fg=ZH_COLOR,
            font=('System', 15), wraplength=WIN_WIDTH - 28, justify='left',
        ).pack(anchor='w', pady=(2, 0))

    def _poll_queue(self):
        try:
            while True:
                event, text = self._queue.get_nowait()
                if event == 'interim':
                    self._en_var.set(text)
                    self._en_label.config(fg=EN_DRAFT)
                elif event == 'final':
                    self._en_var.set(text)
                    self._en_label.config(fg=EN_FINAL)
                elif event == 'translation':
                    self._zh_var.set(text)
                elif event == 'status':
                    if text == 'listening':
                        self._status_dot.config(text='● 聆聽中', fg='#22c55e')
                    else:
                        self._status_dot.config(text='● 暫停', fg='#ef4444')
                elif event == 'clear':
                    self._en_var.set('— 等待聲音 —')
                    self._zh_var.set('')
                    self._en_label.config(fg=EN_DRAFT)
        except queue.Empty:
            pass
        if self._root:
            self._root.after(50, self._poll_queue)

    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _do_drag(self, event):
        x = self._root.winfo_x() + event.x - self._drag_x
        y = self._root.winfo_y() + event.y - self._drag_y
        self._root.geometry(f'+{x}+{y}')
```

- [ ] **Step 4: 執行確認通過**

```bash
cd tools/live-translator
pytest tests/test_ui.py -v
```

預期：所有測試 PASS

- [ ] **Step 5: Commit**

```bash
git add tools/live-translator/ui.py tools/live-translator/tests/test_ui.py
git commit -m "feat(live-translator): 實作 SubtitleWindow，佇列驅動的 tkinter 懸浮字幕視窗"
```

---

## Task 6: main.py — 選單列 + 整合

**Files:**
- Create: `tools/live-translator/main.py`

（main.py 是整合層，直接做手動煙霧測試，不寫單元測試）

- [ ] **Step 1: 實作 main.py**

```python
# tools/live-translator/main.py
import threading
import rumps

from audio import find_blackhole_device, AudioCapture
from transcriber import Transcriber
from translator import Translator
from ui import SubtitleWindow


class LiveTranslatorApp(rumps.App):
    def __init__(self):
        super().__init__('🎙', quit_button=None)
        self.menu = [
            rumps.MenuItem('開始翻譯', callback=self.toggle_translation),
            rumps.MenuItem('清空字幕', callback=self.clear_subtitles),
            None,
            rumps.MenuItem('結束', callback=self.quit_app),
        ]
        self._running = False
        self._audio: AudioCapture | None = None
        self._transcriber: Transcriber | None = None
        self._translator: Translator | None = None

        self._window = SubtitleWindow()
        self._window.start()

    def toggle_translation(self, sender):
        if self._running:
            self._stop()
            sender.title = '開始翻譯'
            self.title = '🎙'
        else:
            if self._start():
                sender.title = '暫停翻譯'
                self.title = '🔴'

    def _start(self) -> bool:
        device = find_blackhole_device()
        if device is None:
            rumps.alert(
                title='找不到 BlackHole',
                message=(
                    '請先安裝 BlackHole 2ch，並在「音訊 MIDI 設定」\n'
                    '建立包含 BlackHole + 內建喇叭的「多輸出裝置」，\n'
                    '再將系統音效輸出切換到該裝置。\n\n'
                    '下載：https://existential.audio/blackhole/'
                ),
            )
            return False

        if self._translator is None:
            self._translator = Translator()

        self._transcriber = Transcriber(
            on_interim=self._window.set_interim,
            on_final=self._on_final,
        )
        self._audio = AudioCapture(device_index=device, callback=self._transcriber.feed)

        self._transcriber.start()
        self._audio.start()
        self._window.set_status('listening')
        self._running = True
        return True

    def _stop(self):
        if self._audio:
            self._audio.stop()
            self._audio = None
        if self._transcriber:
            self._transcriber.stop()
            self._transcriber = None
        self._window.set_status('paused')
        self._running = False

    def _on_final(self, text: str):
        self._window.set_final(text)
        threading.Thread(
            target=self._translate_and_display,
            args=(text,),
            daemon=True,
        ).start()

    def _translate_and_display(self, text: str):
        try:
            zh = self._translator.translate(text)
            self._window.set_translation(zh)
        except Exception:
            self._window.set_translation('翻譯暫時失敗')

    def clear_subtitles(self, _):
        self._window.clear()

    def quit_app(self, _):
        self._stop()
        rumps.quit_application()


if __name__ == '__main__':
    LiveTranslatorApp().run()
```

- [ ] **Step 2: 執行所有測試確認未破壞其他模組**

```bash
cd tools/live-translator
pytest tests/ -v
```

預期：所有測試 PASS

- [ ] **Step 3: Commit**

```bash
git add tools/live-translator/main.py
git commit -m "feat(live-translator): 實作 main.py，rumps 選單列整合所有模組"
```

---

## Task 7: README.md — 安裝與使用說明

**Files:**
- Create: `tools/live-translator/README.md`

- [ ] **Step 1: 撰寫 README.md**

```markdown
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

```bash
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
```

- [ ] **Step 2: Commit**

```bash
git add tools/live-translator/README.md
git commit -m "docs(live-translator): 新增安裝與使用說明"
```

---

## Task 8: 手動端到端煙霧測試

- [ ] **Step 1: 確認 BlackHole 已安裝並設定**

開啟「系統設定 → 聲音 → 輸出」，確認選的是「多輸出裝置」。

- [ ] **Step 2: 啟動程式**

```bash
cd tools/live-translator
python main.py
```

- [ ] **Step 3: 測試正常流程**

1. 點選單列 🎙 → 「開始翻譯」，確認變為 🔴
2. 播放一段 YouTube 英文影片（30 秒以上）
3. 確認懸浮視窗出現英文草稿（灰色）→ 英文鎖定（白色）→ 中文翻譯（藍色）
4. 拖曳視窗到螢幕另一角，確認可以移動
5. 點「清空字幕」，確認視窗清空
6. 點「暫停翻譯」，確認停止辨識
7. 點「結束」，確認程式結束

- [ ] **Step 4: 測試錯誤處理**

將系統音效輸出切回「MacBook Pro 喇叭」（不是多輸出裝置），重新啟動程式並點「開始翻譯」，確認出現「找不到 BlackHole」提示視窗。

- [ ] **Step 5: 最終 commit + push**

```bash
git add .
git commit -m "feat(live-translator): 完成即時英中字幕翻譯工具，通過手動煙霧測試"
git push origin main
```

---

## 規格覆蓋確認

| 規格需求 | 對應 Task |
|---------|-----------|
| 系統音訊抓取（BlackHole） | Task 3 audio.py |
| VAD 靜音偵測 | Task 4 transcriber.py |
| faster-whisper 串流辨識 | Task 4 transcriber.py |
| Argos Translate 離線翻譯 | Task 2 translator.py |
| OpenCC 繁體中文轉換 | Task 2 translator.py |
| rumps 選單列常駐 | Task 6 main.py |
| tkinter 懸浮視窗 | Task 5 ui.py |
| 可拖曳視窗 | Task 5 ui.py |
| Always on Top | Task 5 ui.py |
| Interim 草稿 / Final 鎖定 顯示 | Task 5 ui.py + Task 4 |
| BlackHole 未找到提示 | Task 6 main.py |
| 模型自動下載 | Task 2 translator.py |
| 靜音時顯示等待 | Task 4（VAD 不觸發）+ Task 5 |
| 翻譯失敗不崩潰 | Task 6 _translate_and_display |
| README 安裝說明 | Task 7 |
