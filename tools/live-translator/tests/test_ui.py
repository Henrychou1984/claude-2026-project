# tests/test_ui.py
import queue as queue_module


def test_set_interim_enqueues_interim_event():
    from ui import SubtitleWindow
    win = SubtitleWindow()
    win.set_interim('hello world')
    event, text = win._queue.get_nowait()
    assert event == 'interim'
    assert 'hello world' in text


def test_set_final_enqueues_final_event():
    from ui import SubtitleWindow
    win = SubtitleWindow()
    win.set_final('confirmed sentence')
    event, text = win._queue.get_nowait()
    assert event == 'final'
    assert text == 'confirmed sentence'


def test_set_translation_enqueues_translation_event():
    from ui import SubtitleWindow
    win = SubtitleWindow()
    win.set_translation('翻譯結果')
    event, text = win._queue.get_nowait()
    assert event == 'translation'
    assert text == '翻譯結果'


def test_clear_enqueues_clear_event():
    from ui import SubtitleWindow
    win = SubtitleWindow()
    win.clear()
    event, text = win._queue.get_nowait()
    assert event == 'clear'


def test_set_status_enqueues_status_event():
    from ui import SubtitleWindow
    win = SubtitleWindow()
    win.set_status('listening')
    event, text = win._queue.get_nowait()
    assert event == 'status'
    assert text == 'listening'
