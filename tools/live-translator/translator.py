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
