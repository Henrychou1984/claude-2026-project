import threading
import tkinter.messagebox as msgbox

from audio import find_blackhole_device, AudioCapture
from transcriber import Transcriber
from translator import Translator
from ui import SubtitleWindow


class LiveTranslator:
    def __init__(self):
        self._running = False
        self._audio: AudioCapture | None = None
        self._transcriber: Transcriber | None = None
        self._translator: Translator | None = None

        self._window = SubtitleWindow(
            on_toggle=self.toggle,
            on_quit=self._stop,
        )

    def toggle(self):
        if self._running:
            self._stop()
        else:
            self._start()

    def _start(self):
        device = find_blackhole_device()
        if device is None:
            msgbox.showwarning(
                '找不到 BlackHole',
                '請先安裝 BlackHole 2ch，並在「音訊 MIDI 設定」\n'
                '建立包含 BlackHole + 內建喇叭的「多輸出裝置」，\n'
                '再將系統音效輸出切換到該裝置。\n\n'
                '下載：https://existential.audio/blackhole/',
            )
            return

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
        self._window.update_toggle_label(is_running=True)
        self._running = True

    def _stop(self):
        if self._audio:
            self._audio.stop()
            self._audio = None
        if self._transcriber:
            self._transcriber.stop()
            self._transcriber = None
        self._window.set_status('paused')
        self._window.update_toggle_label(is_running=False)
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

    def run(self):
        """主執行緒進入點：啟動 tkinter（blocking）。"""
        self._window.run()


if __name__ == '__main__':
    LiveTranslator().run()
