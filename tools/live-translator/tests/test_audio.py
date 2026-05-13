# tests/test_audio.py
from unittest.mock import patch, MagicMock
import numpy as np


def test_find_blackhole_device_returns_index_when_found():
    mock_devices = [
        {'name': 'Built-in Microphone', 'max_input_channels': 2},
        {'name': 'BlackHole 2ch', 'max_input_channels': 2},
        {'name': 'Built-in Output', 'max_input_channels': 0},
    ]
    with patch('sounddevice.query_devices', return_value=mock_devices):
        from audio import find_blackhole_device
        idx = find_blackhole_device()
    assert idx == 1


def test_find_blackhole_device_returns_none_when_not_found():
    mock_devices = [
        {'name': 'Built-in Microphone', 'max_input_channels': 2},
        {'name': 'Built-in Output', 'max_input_channels': 0},
    ]
    with patch('sounddevice.query_devices', return_value=mock_devices):
        from audio import find_blackhole_device
        idx = find_blackhole_device()
    assert idx is None


def test_find_blackhole_device_ignores_output_only_devices():
    mock_devices = [
        {'name': 'BlackHole 2ch', 'max_input_channels': 0},
    ]
    with patch('sounddevice.query_devices', return_value=mock_devices):
        from audio import find_blackhole_device
        idx = find_blackhole_device()
    assert idx is None


def test_audio_capture_callback_passes_mono_chunk():
    from audio import AudioCapture
    received = []
    capture = AudioCapture(device_index=1, callback=received.append)

    fake_indata = np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]], dtype='float32')
    capture._audio_callback(fake_indata, 3, None, None)

    assert len(received) == 1
    assert received[0].ndim == 1
    assert len(received[0]) == 3
    np.testing.assert_array_almost_equal(received[0], [0.1, 0.3, 0.5])
