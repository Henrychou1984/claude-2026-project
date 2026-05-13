import numpy as np
import threading
import time
from faster_whisper import WhisperModel
from typing import Callable

SAMPLE_RATE = 16000
INTERIM_EVERY = 1.0
SILENCE_AFTER = 0.5
MAX_BUFFER_SECONDS = 30
FORCE_FINAL_AFTER = 2  # 連續說話超過 2 秒就強制送出翻譯


class Transcriber:
    def __init__(
        self,
        on_interim: Callable[[str], None],
        on_final: Callable[[str], None],
        model_size: str = 'small',
    ):
        self._on_interim = on_interim
        self._on_final = on_final
        self._model = WhisperModel(model_size, device='cpu', compute_type='int8',
                                   num_workers=2)
        self._buffer = np.array([], dtype='float32')
        self._lock = threading.Lock()
        self._last_feed_time: float | None = None
        self._last_interim_time: float = 0.0
        self._buffer_start: float | None = None
        self._running = False
        self._thread: threading.Thread | None = None

    def feed(self, chunk: np.ndarray):
        with self._lock:
            if len(self._buffer) == 0:
                self._buffer_start = time.time()
            self._buffer = np.concatenate([self._buffer, chunk])
            max_samples = SAMPLE_RATE * MAX_BUFFER_SECONDS
            if len(self._buffer) > max_samples:
                self._buffer = self._buffer[-max_samples:]
            self._last_feed_time = time.time()

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self):
        while self._running:
            now = time.time()

            with self._lock:
                buf = self._buffer.copy()
                last_feed = self._last_feed_time

            has_audio = len(buf) >= SAMPLE_RATE * 0.5

            if has_audio and now - self._last_interim_time >= INTERIM_EVERY:
                text = self._transcribe(buf)
                if text:
                    self._on_interim(text)
                self._last_interim_time = now

            buffer_age = (now - self._buffer_start) if self._buffer_start else 0
            silence = has_audio and last_feed and now - last_feed >= SILENCE_AFTER
            force = has_audio and buffer_age >= FORCE_FINAL_AFTER

            if silence or force:
                text = self._transcribe(buf)
                if text:
                    self._on_final(text)
                with self._lock:
                    self._buffer = np.array([], dtype='float32')
                    self._last_feed_time = None
                    self._buffer_start = None
                self._last_interim_time = 0.0

            time.sleep(0.1)

    def _transcribe(self, audio: np.ndarray) -> str:
        segments, _ = self._model.transcribe(
            audio,
            language='en',
            vad_filter=True,
            beam_size=1,
        )
        return ' '.join(s.text.strip() for s in segments).strip()
