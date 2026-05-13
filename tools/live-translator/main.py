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
