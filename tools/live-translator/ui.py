import threading
import queue
try:
    import tkinter as tk
    _HAS_TK = True
except (ImportError, ModuleNotFoundError):
    tk = None  # type: ignore[assignment]
    _HAS_TK = False

BG = '#0f172a'
TITLE_BG = '#1e293b'
EN_DRAFT = '#94a3b8'
EN_FINAL = '#e2e8f0'
ZH_COLOR = '#38bdf8'
LABEL_COLOR = '#475569'
WIN_WIDTH = 340


class SubtitleWindow:
    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._root = None
        self._en_var = None
        self._zh_var = None
        self._en_label = None
        self._status_dot = None
        self._drag_x = 0
        self._drag_y = 0

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

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
