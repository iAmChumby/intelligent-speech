"""TranscriptionEngine: background WhisperModel loading with warmup and device detection.

Loads faster-whisper's WhisperModel in a daemon background thread at construction time.
Thread-safe: ``transcribe()`` and ``transcribe_file()`` block until the model is ready.
The warmup inference (1-second silence) amortizes CUDA JIT compilation cost during startup
rather than during the first user recording.
"""
import threading
import time
from typing import Optional

import numpy as np

from faster_whisper import WhisperModel


# Valid compute types for Blackwell (sm_120) — INT8 variants are not supported.
_BLACKWELL_COMPUTE_TYPES = frozenset({"float16", "float32", "bfloat16"})


class TranscriptionEngine:
    """Loads WhisperModel in a background thread at construction.

    Thread-safe: transcribe() blocks until model is ready.
    """

    def __init__(
        self,
        model_size: str = "large-v3-turbo",
        device: str = "cuda",
        compute_type: str = "float16",
    ) -> None:
        # Blackwell compute_type guard (Pitfall 1 — RESEARCH.md)
        # INT8 variants raise CUBLAS_STATUS_NOT_SUPPORTED on sm_120.
        # CPU allows any compute_type (int8 is valid for CPU fallback).
        if device == "cuda" and compute_type not in _BLACKWELL_COMPUTE_TYPES:
            raise ValueError(
                f"compute_type '{compute_type}' is not supported on Blackwell (sm_120). "
                f"Use float16, float32, or bfloat16."
            )

        self._model: Optional[WhisperModel] = None
        self._actual_device: Optional[str] = None
        self._ready = threading.Event()
        self._load_error: Optional[Exception] = None

        self._thread = threading.Thread(
            target=self._load_model,
            args=(model_size, device, compute_type),
            daemon=True,
            name="WhisperModelLoader",
        )
        self._thread.start()

    def _load_model(self, model_size: str, device: str, compute_type: str) -> None:
        """Load the WhisperModel, run warmup inference, and signal readiness.

        Runs in the daemon background thread named "WhisperModelLoader".
        Always sets self._ready in the finally block — callers must check
        self._load_error to distinguish success from failure.
        """
        t0 = time.perf_counter()
        try:
            model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
            )
            # Read the actual device from the underlying ctranslate2 model.
            # model.model is a ctranslate2.models.Whisper instance with a .device property.
            self._actual_device = model.model.device

            # Warmup: feed 1 second of silence to trigger CUDA JIT compilation.
            # This prevents the first real recording from having extra latency (Pitfall 5).
            silence = np.zeros(16000, dtype=np.float32)
            list(model.transcribe(silence, beam_size=1, language="en")[0])

            self._model = model
            elapsed = time.perf_counter() - t0
            print(
                f"[MODEL] Loaded on {self._actual_device} in {elapsed:.1f}s "
                f"(warmup included)"
            )

        except Exception as exc:
            self._load_error = exc
            print(f"[MODEL ERROR] {exc}")
        finally:
            self._ready.set()  # Always signal — caller checks _load_error

    @property
    def is_ready(self) -> bool:
        """Return True if the model has finished loading (success or failure)."""
        return self._ready.is_set()

    @property
    def actual_device(self) -> Optional[str]:
        """The device the WhisperModel is actually running on ('cuda' or 'cpu').

        Returns None if the model has not finished loading yet.
        """
        return self._actual_device

    def wait_until_ready(self, timeout: float = 60.0) -> bool:
        """Block until the model is loaded. Returns True if ready, False on timeout."""
        return self._ready.wait(timeout=timeout)

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe a float32 numpy array at 16000 Hz.

        Blocks until the model is ready. Raises the original exception if
        model loading failed.
        """
        self._ready.wait()
        if self._load_error is not None:
            raise self._load_error

        segments, _ = self._model.transcribe(
            audio,
            beam_size=5,
            language="en",
            vad_filter=True,
        )
        return " ".join(s.text for s in segments).strip()

    def transcribe_file(self, path: str) -> str:
        """Transcribe an audio file by path.

        faster-whisper accepts file paths directly (via PyAV/ffmpeg) — no
        manual WAV decoding needed. Blocks until the model is ready.
        """
        self._ready.wait()
        if self._load_error is not None:
            raise self._load_error

        segments, _ = self._model.transcribe(
            path,
            beam_size=5,
            language="en",
        )
        return " ".join(s.text for s in segments).strip()
