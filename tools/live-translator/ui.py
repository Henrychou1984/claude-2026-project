import queue
import tkinter as tk
from typing import Callable

BG = '#0f172a'
TITLE_BG = '#1e293b'
EN_DRAFT = '#94a3b8'
EN_FINAL = '#e2e8f0'
ZH_COLOR = '#38bdf8'
LABEL_COLOR = '#475569'
WIN_WIDTH = 360


class SubtitleWindow:
    """tkinter 懸浮字幕視窗（必須在主執行緒呼叫 run()）"""

    def __init__(
        self,
        on_toggle: Callable[[], None] | None = None,
        on_quit: Callable[[], None] | None = None,
    ):
        self._queue: queue.Queue = queue.Queue()
        self._on_toggle = on_toggle or (lambda: None)
        self._on_quit = on_quit or (lambda: None)

        self._root: tk.Tk | None = None
        self._en_var: tk.StringVar | None = None
        self._zh_var: tk.StringVar | None = None
        self._en_label: tk.Label | None = None
        self._status_dot: tk.Label | None = None
        self._toggle_btn: tk.Button | None = None
        self._drag_x = 0
        self._drag_y = 0

    # ── 公開佇列方法（任何執行緒皆可呼叫）──────────────────────

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

    def update_toggle_label(self, is_running: bool):
        self._queue.put(('toggle_label', 'running' if is_running else 'stopped'))

    # ── 主執行緒進入點 ──────────────────────────────────────────

    def run(self):
        """在主執行緒呼叫，啟動 tkinter event loop（blocking）。"""
        self._root = tk.Tk()
        self._root.overrideredirect(True)
        self._root.wm_attributes('-topmost', True)
        self._root.wm_attributes('-alpha', 0.90)
        self._root.configure(bg=BG)

        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        self._root.geometry(f'{WIN_WIDTH}x230+{sw - WIN_WIDTH - 20}+{sh - 270}')

        self._build_ui()
        self._root.after(50, self._poll_queue)
        self._root.mainloop()

    def close(self):
        if self._root:
            self._root.quit()

    # ── UI 建構 ─────────────────────────────────────────────────

    def _build_ui(self):
        # 標題列
        title_bar = tk.Frame(self._root, bg=TITLE_BG, height=34)
        title_bar.pack(fill='x')
        title_bar.bind('<Button-1>', self._start_drag)
        title_bar.bind('<B1-Motion>', self._do_drag)

        # 左側：標題
        tk.Label(
            title_bar, text='即時翻譯', bg=TITLE_BG, fg=LABEL_COLOR,
            font=('System', 10),
        ).pack(side='left', padx=10, pady=6)

        # 右側：結束按鈕
        tk.Button(
            title_bar, text='✕', bg=TITLE_BG, fg='#64748b',
            font=('System', 11), relief='flat', padx=6, pady=0,
            activebackground='#ef4444', activeforeground='#fff',
            command=self._handle_quit,
        ).pack(side='right', padx=4, pady=4)

        # 右側：清空按鈕
        tk.Button(
            title_bar, text='清空', bg=TITLE_BG, fg='#64748b',
            font=('System', 9), relief='flat', padx=6, pady=0,
            activebackground='#334155', activeforeground='#fff',
            command=lambda: self.clear(),
        ).pack(side='right', padx=2, pady=4)

        # 右側：開始/暫停按鈕
        self._toggle_btn = tk.Button(
            title_bar, text='▶ 開始', bg='#1e3a5f', fg='#93c5fd',
            font=('System', 9), relief='flat', padx=8, pady=0,
            activebackground='#1d4ed8', activeforeground='#fff',
            command=self._handle_toggle,
        )
        self._toggle_btn.pack(side='right', padx=4, pady=4)

        # 狀態點
        self._status_dot = tk.Label(
            title_bar, text='● 待機', bg=TITLE_BG, fg='#475569',
            font=('System', 9),
        )
        self._status_dot.pack(side='left', padx=4)

        # 內容區
        content = tk.Frame(self._root, bg=BG, padx=14, pady=10)
        content.pack(fill='both', expand=True)

        tk.Label(content, text='EN', bg=BG, fg=LABEL_COLOR, font=('System', 9)).pack(anchor='w')

        self._en_var = tk.StringVar(value='— 點「▶ 開始」來翻譯 —')
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

    # ── 佇列輪詢（主執行緒 after() callback）──────────────────

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
                elif event == 'toggle_label':
                    if text == 'running':
                        self._toggle_btn.config(text='⏸ 暫停', bg='#1e3a5f', fg='#fca5a5')
                    else:
                        self._toggle_btn.config(text='▶ 開始', bg='#1e3a5f', fg='#93c5fd')
                elif event == 'clear':
                    self._en_var.set('— 等待聲音 —')
                    self._zh_var.set('')
                    self._en_label.config(fg=EN_DRAFT)
        except queue.Empty:
            pass
        if self._root:
            self._root.after(50, self._poll_queue)

    # ── 按鈕回呼 ────────────────────────────────────────────────

    def _handle_toggle(self):
        self._on_toggle()

    def _handle_quit(self):
        self._on_quit()
        self.close()

    # ── 拖曳 ────────────────────────────────────────────────────

    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _do_drag(self, event):
        x = self._root.winfo_x() + event.x - self._drag_x
        y = self._root.winfo_y() + event.y - self._drag_y
        self._root.geometry(f'+{x}+{y}')
