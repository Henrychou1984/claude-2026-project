# tests/test_transcriber.py
from unittest.mock import MagicMock, patch
import numpy as np
import time
import sys

# Mock faster_whisper at module level so all imports succeed
_mock_fw = MagicMock()
sys.modules.setdefault('faster_whisper', _mock_fw)


def make_transcriber(on_interim=None, on_final=None):
    # Remove cached transcriber so each call gets a fresh instance
    sys.modules.pop('transcriber', None)
    with patch('faster_whisper.WhisperModel', return_value=MagicMock()):
        from transcriber import Transcriber
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


def test_transcribe_joins_multiple_segments():
    t = make_transcriber()
    seg1 = MagicMock()
    seg1.text = ' Hello '
    seg2 = MagicMock()
    seg2.text = ' world '
    t._model.transcribe.return_value = ([seg1, seg2], MagicMock())
    result = t._transcribe(np.zeros(16000, dtype='float32'))
    assert result == 'Hello world'


def test_on_final_called_after_silence():
    on_final = MagicMock()
    t = make_transcriber(on_final=on_final)

    seg = MagicMock()
    seg.text = 'Test sentence'
    t._model.transcribe.return_value = ([seg], MagicMock())

    chunk = np.zeros(8000, dtype='float32')
    t.feed(chunk)

    import transcriber as tr_module
    t._last_feed_time = time.time() - tr_module.SILENCE_AFTER - 0.1

    t.start()
    time.sleep(0.5)
    t.stop()

    on_final.assert_called_once_with('Test sentence')
