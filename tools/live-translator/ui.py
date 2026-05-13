import queue
import tkinter as tk
from typing import Callable

BG = '#0f172a'
TITLE_BG = '#1e293b'
EN_DRAFT = '#94a3b8'
EN_FINAL = '#e2e8f0'
ZH_COLOR = '#38bdf8'
LABEL_COLOR = '#475569'
WIN_WIDTH = 400


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
        self._history_text: tk.Text | None = None
        self._interim_var: tk.StringVar | None = None
        self._status_dot: tk.Label | None = None
        self._toggle_btn: tk.Button | None = None
        self._pending_final: str = ''
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
        self._root.geometry(f'{WIN_WIDTH}x500+{sw - WIN_WIDTH - 20}+{sh - 540}')

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

        tk.Label(
            title_bar, text='即時翻譯', bg=TITLE_BG, fg=LABEL_COLOR,
            font=('System', 10),
        ).pack(side='left', padx=10, pady=6)

        tk.Button(
            title_bar, text='✕', bg=TITLE_BG, fg='#64748b',
            font=('System', 11), relief='flat', padx=6, pady=0,
            activebackground='#ef4444', activeforeground='#fff',
            command=self._handle_quit,
        ).pack(side='right', padx=4, pady=4)

        tk.Button(
            title_bar, text='清空', bg=TITLE_BG, fg='#64748b',
            font=('System', 9), relief='flat', padx=6, pady=0,
            activebackground='#334155', activeforeground='#fff',
            command=lambda: self.clear(),
        ).pack(side='right', padx=2, pady=4)

        self._toggle_btn = tk.Button(
            title_bar, text='▶ 開始', bg='#1e3a5f', fg='#93c5fd',
            font=('System', 9), relief='flat', padx=8, pady=0,
            activebackground='#1d4ed8', activeforeground='#fff',
            command=self._handle_toggle,
        )
        self._toggle_btn.pack(side='right', padx=4, pady=4)

        self._status_dot = tk.Label(
            title_bar, text='● 待機', bg=TITLE_BG, fg='#475569',
            font=('System', 9),
        )
        self._status_dot.pack(side='left', padx=4)

        # 歷史捲動區
        self._history_text = tk.Text(
            self._root, bg=BG, relief='flat', wrap='word',
            state='disabled', cursor='arrow',
            padx=14, pady=10, spacing3=6,
            font=('System', 12),
        )
        self._history_text.pack(fill='both', expand=True)
        self._history_text.tag_configure('en_lbl', foreground=LABEL_COLOR, font=('System', 9))
        self._history_text.tag_configure('zh_lbl', foreground='#1d4ed8', font=('System', 9))
        self._history_text.tag_configure('en', foreground=EN_FINAL, font=('System', 13))
        self._history_text.tag_configure('zh', foreground=ZH_COLOR, font=('System', 15))

        # 底部即時辨識列
        tk.Frame(self._root, bg='#1e293b', height=1).pack(fill='x')
        self._interim_var = tk.StringVar(value='— 點「▶ 開始」來翻譯 —')
        tk.Label(
            self._root, textvariable=self._interim_var,
            bg='#0d1b2e', fg=EN_DRAFT, font=('System', 11),
            wraplength=WIN_WIDTH - 28, justify='left',
            padx=14, pady=8, anchor='w',
        ).pack(fill='x')

    # ── 歷史追加 ────────────────────────────────────────────────

    def _append_to_history(self, en: str, zh: str):
        t = self._history_text
        t.config(state='normal')
        existing = t.get('1.0', 'end').strip()
        if existing:
            t.insert('end', '\n\n')
        if en:
            t.insert('end', 'EN\n', 'en_lbl')
            t.insert('end', en + '\n', 'en')
        if zh:
            t.insert('end', '中文\n', 'zh_lbl')
            t.insert('end', zh, 'zh')
        t.config(state='disabled')
        t.see('end')

    # ── 佇列輪詢（主執行緒 after() callback）──────────────────

    def _poll_queue(self):
        try:
            while True:
                event, text = self._queue.get_nowait()
                if event == 'interim':
                    self._interim_var.set(text)
                elif event == 'final':
                    self._pending_final = text
                    self._interim_var.set(text)
                elif event == 'translation':
                    self._append_to_history(self._pending_final, text)
                    self._interim_var.set('')
                    self._pending_final = ''
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
                    self._history_text.config(state='normal')
                    self._history_text.delete('1.0', 'end')
                    self._history_text.config(state='disabled')
                    self._interim_var.set('— 等待聲音 —')
                    self._pending_final = ''
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
