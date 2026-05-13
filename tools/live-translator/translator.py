from deep_translator import GoogleTranslator


class Translator:
    def __init__(self):
        self._gt = GoogleTranslator(source='en', target='zh-TW')

    def translate(self, text: str) -> str:
        if not text.strip():
            return ''
        return self._gt.translate(text)
