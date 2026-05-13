import sounddevice as sd
import numpy as np
from typing import Callable, Optional

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 0.5
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
BLACKHOLE_KEYWORDS = ['blackhole']


def find_blackhole_device() -> Optional[int]:
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if any(kw in d['name'].lower() for kw in BLACKHOLE_KEYWORDS):
            if d['max_input_channels'] > 0:
                return i
    return None


class AudioCapture:
    def __init__(self, device_index: int, callback: Callable[[np.ndarray], None]):
        self._device = device_index
        self._callback = callback
        self._stream = None

    def start(self):
        self._stream = sd.InputStream(
            device=self._device,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='float32',
            blocksize=CHUNK_SIZE,
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop(self):
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def _audio_callback(self, indata: np.ndarray, frames: int, time, status):
        self._callback(indata[:, 0].copy())
