# tests/test_translator.py
import sys
from unittest.mock import patch, MagicMock


class MockPkg:
    """Simple class to represent a package with from_code and to_code attributes"""
    def __init__(self, from_code='en', to_code='zh'):
        self.from_code = from_code
        self.to_code = to_code


def _setup_mocks():
    """Helper to set up all required mocks with proper module hierarchy"""
    mock_pkg = MockPkg('en', 'zh')

    # Create mock modules with proper hierarchy
    mock_argos_package = MagicMock()
    mock_argos_package.get_installed_packages.return_value = [mock_pkg]

    mock_argos_translate = MagicMock()
    mock_argos_translate.translate.return_value = '测试'

    # Create parent module and set up hierarchy
    mock_argostranslate = MagicMock()
    mock_argostranslate.package = mock_argos_package
    mock_argostranslate.translate = mock_argos_translate

    mock_opencc = MagicMock()
    mock_opencc_instance = MagicMock()
    mock_opencc_instance.convert.return_value = '測試'
    mock_opencc.OpenCC.return_value = mock_opencc_instance

    return {
        'argostranslate': mock_argostranslate,
        'argostranslate.package': mock_argos_package,
        'argostranslate.translate': mock_argos_translate,
        'opencc': mock_opencc,
    }, mock_argos_translate, mock_opencc_instance


def test_translate_calls_argos_with_correct_language_codes():
    """確認翻譯時呼叫 argostranslate.translate.translate('text', 'en', 'zh')"""
    modules, mock_argos_translate, mock_opencc_instance = _setup_mocks()

    with patch.dict(sys.modules, modules):
        if 'translator' in sys.modules:
            del sys.modules['translator']

        from translator import Translator
        t = Translator()
        result = t.translate('test input')

        # Verify the correct functions were called
        mock_argos_translate.translate.assert_called_once_with('test input', 'en', 'zh')
        mock_opencc_instance.convert.assert_called_once_with('测试')
        assert result == '測試'


def test_translate_applies_opencc_s2t():
    """確認翻譯結果經過 OpenCC s2t 轉換"""
    mock_pkg = MockPkg('en', 'zh')

    mock_argos_package = MagicMock()
    mock_argos_package.get_installed_packages.return_value = [mock_pkg]

    mock_argos_translate = MagicMock()
    mock_argos_translate.translate.return_value = '这个功能帮助学生'

    mock_argostranslate = MagicMock()
    mock_argostranslate.package = mock_argos_package
    mock_argostranslate.translate = mock_argos_translate

    mock_opencc = MagicMock()
    mock_opencc_instance = MagicMock()
    mock_opencc_instance.convert.return_value = '這個功能幫助學生'
    mock_opencc.OpenCC.return_value = mock_opencc_instance

    with patch.dict(sys.modules, {
        'argostranslate': mock_argostranslate,
        'argostranslate.package': mock_argos_package,
        'argostranslate.translate': mock_argos_translate,
        'opencc': mock_opencc,
    }):
        if 'translator' in sys.modules:
            del sys.modules['translator']

        from translator import Translator
        t = Translator()
        result = t.translate('This feature helps students')

        # Verify OpenCC was called with the simplified Chinese from argostranslate
        mock_opencc_instance.convert.assert_called_once_with('这个功能帮助学生')
        assert result == '這個功能幫助學生'


def test_translate_empty_string_returns_empty():
    """空字串輸入應直接回傳空字串，不呼叫翻譯 API"""
    mock_pkg = MockPkg('en', 'zh')

    mock_argos_package = MagicMock()
    mock_argos_package.get_installed_packages.return_value = [mock_pkg]

    mock_argos_translate = MagicMock()

    mock_argostranslate = MagicMock()
    mock_argostranslate.package = mock_argos_package
    mock_argostranslate.translate = mock_argos_translate

    mock_opencc = MagicMock()
    mock_opencc_instance = MagicMock()
    mock_opencc.OpenCC.return_value = mock_opencc_instance

    with patch.dict(sys.modules, {
        'argostranslate': mock_argostranslate,
        'argostranslate.package': mock_argos_package,
        'argostranslate.translate': mock_argos_translate,
        'opencc': mock_opencc,
    }):
        if 'translator' in sys.modules:
            del sys.modules['translator']

        from translator import Translator
        t = Translator()
        result = t.translate('')

        # Translate should NOT be called for empty input
        mock_argos_translate.translate.assert_not_called()
        assert result == ''


def test_translate_whitespace_only_returns_empty():
    """只有空白的輸入應回傳空字串"""
    mock_pkg = MockPkg('en', 'zh')

    mock_argos_package = MagicMock()
    mock_argos_package.get_installed_packages.return_value = [mock_pkg]

    mock_argos_translate = MagicMock()

    mock_argostranslate = MagicMock()
    mock_argostranslate.package = mock_argos_package
    mock_argostranslate.translate = mock_argos_translate

    mock_opencc = MagicMock()
    mock_opencc_instance = MagicMock()
    mock_opencc.OpenCC.return_value = mock_opencc_instance

    with patch.dict(sys.modules, {
        'argostranslate': mock_argostranslate,
        'argostranslate.package': mock_argos_package,
        'argostranslate.translate': mock_argos_translate,
        'opencc': mock_opencc,
    }):
        if 'translator' in sys.modules:
            del sys.modules['translator']

        from translator import Translator
        t = Translator()
        result = t.translate('   ')

        # Translate should NOT be called for whitespace-only input
        mock_argos_translate.translate.assert_not_called()
        assert result == ''
