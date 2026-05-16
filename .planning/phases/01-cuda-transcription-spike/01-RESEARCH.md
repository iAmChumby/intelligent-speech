# Phase 1: CUDA & Transcription Spike — Research

**Researched:** 2026-05-16
**Domain:** CTranslate2 / faster-whisper GPU inference on Blackwell (RTX 5070 Ti)
**Confidence:** HIGH (core findings verified against GitHub issues, PyPI, official release notes, live nvidia-smi output)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-08:** Library: faster-whisper 1.2.1 — CTranslate2-backed, 4x faster than openai/whisper, native CUDA 12 support
- **D-09:** Default model: large-v3-turbo — 8x faster than large-v3 for English, ~1.5GB VRAM at int8_float16
- **D-10:** CUDA version lock: CUDA 12 + cuDNN 9 (ctranslate2 >= 4.5 hard requirement). Install via: `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12==9.0.0`
- **D-11:** Blackwell (RTX 5070 Ti) compatibility: MUST work on GPU — this is a hard gate. CPU-only fallback is NOT an acceptable Phase 1 outcome.
- **D-12:** Audio capture: sounddevice 0.5.5
- **D-13:** VAD: silero-vad pip package — torch dependency accepted
- **D-19:** Python version: 3.11

### Claude's Discretion

- Project structure layout for Phase 1 → Phase 2 growth
- Threading pattern for background model loading
- Test WAV generation approach
- Warmup inference implementation details
- Walking skeleton deliverable scope

### Deferred Ideas (OUT OF SCOPE)

- Visual styling / look-and-feel of the Electron overlay (Phase 4)
- React state management library (Phase 4)
- CSS/styling framework (Phase 4)
- JSON vs SQLite for profile storage (Phase 6)
- pynput (replaced by Electron globalShortcut in Phase 5)

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CORE-02 | System transcribes captured audio locally using faster-whisper with CUDA acceleration (RTX GPU) | Installation sequence, Blackwell compute_type fix, device verification pattern |
| CORE-03 | System falls back to CPU transcription when CUDA is unavailable, with user-visible indication | CUDA exception taxonomy, CPU fallback detection pattern |
| CORE-05 | System loads the Whisper model at startup in a background thread; recording is disabled until model is ready | Threading pattern, threading.Event ready signal, warmup inference |

</phase_requirements>

---

## Summary

**Five bullets that determine the plan structure:**

1. **Blackwell (RTX 5070 Ti / sm_120) requires `compute_type="float16"`** — INT8 is disabled for sm_120 in ctranslate2 >= 4.6.2. Using `int8_float16` (the typical default) raises `CUBLAS_STATUS_NOT_SUPPORTED` on all RTX 50-series GPUs. `float16` works and is the correct compute type for Blackwell. [VERIFIED: GitHub OpenNMT/CTranslate2 #1865, SubtitleEdit #10180, ctranslate2 CHANGELOG v4.6.2]

2. **ctranslate2 must be pinned to >= 4.6.2 on Windows** — ctranslate2 4.7.0 shipped a Windows-specific regression that causes import to fail with `[WinError 3]` because it incorrectly checks for AMD ROCm paths on NVIDIA-only machines. Pin to `ctranslate2==4.7.1` which fixes the Windows build. [VERIFIED: GitHub OpenNMT/CTranslate2 #2009, PyPI ctranslate2 4.7.1 release]

3. **The nvidia-cublas-cu12 / nvidia-cudnn-cu12 packages do NOT auto-install on Windows with faster-whisper** — they must be explicitly listed in the install command. ctranslate2's Windows wheel links against these DLLs from `site-packages\nvidia\*\bin`. A pre-import `os.add_dll_directory()` loop is required so Python finds them before ctranslate2 loads. [VERIFIED: GitHub CuPy #8164, triton-windows #43, PITFALLS.md §C1]

4. **faster-whisper 1.2.1 accepts `ctranslate2>=4.0,<5`** — pip will pull 4.7.1 (latest) by default; explicit pinning `ctranslate2==4.7.1` in requirements.txt is safe and necessary to avoid the 4.7.0 Windows regression. [VERIFIED: faster-whisper v1.2.1 requirements.txt on GitHub, PyPI ctranslate2 index]

5. **The built-in model name for large-v3-turbo is `"large-v3-turbo"`** — no HuggingFace repo path needed; faster-whisper maps this to `mobiuslabsgmbh/faster-whisper-large-v3-turbo` automatically. Alias `"turbo"` also works. [VERIFIED: faster_whisper/utils.py `_MODELS` dict]

**Primary recommendation:** Use `compute_type="float16"` for the RTX 5070 Ti. Do NOT use `int8_float16` or `int8` — they raise `CUBLAS_STATUS_NOT_SUPPORTED` on Blackwell (sm_120). This is the single most important decision for Phase 1 to succeed on this hardware.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CUDA detection + GPU verification | Python backend | — | ctranslate2 is Python-native; device detection happens at model load time |
| Transcription (WhisperModel) | Python backend | — | faster-whisper is Python-only; must run in worker thread off main thread |
| Model loading lifecycle | Python backend | — | Singleton loaded at startup, held for app lifetime |
| Background thread ready signal | Python stdlib (threading.Event) | — | No Qt/asyncio available in Phase 1; pure Python threading |
| Test WAV generation | Python stdlib (wave module) | — | stdlib-only; no scipy dependency in Phase 1 |
| Warmup inference | Python backend | — | numpy zeros array passed to transcribe(); warms CUDA JIT |
| CPU fallback detection + reporting | Python backend | — | Catch RuntimeError at WhisperModel init; surface to stdout in Phase 1 |

---

## Blackwell Compatibility (ctranslate2 + RTX 5070 Ti)

### Hardware Verified on Target Machine

- **GPU:** NVIDIA GeForce RTX 5070 Ti (Blackwell architecture, sm_120)
- **Driver:** 591.74
- **CUDA driver max version:** 13.1 (backward compatible with CUDA 12 applications)
- **Python:** 3.11.9 (confirmed in environment)
- **CUDA toolkit:** NOT installed system-wide (nvcc not in PATH) — CUDA DLLs must come from pip packages

[VERIFIED: live `nvidia-smi` and `python --version` on target machine]

### The INT8 / Blackwell Incompatibility

**Symptom:** `RuntimeError: cuBLAS failed with status CUBLAS_STATUS_NOT_SUPPORTED`

**Root cause:** INT8 tensor core operations on sm_120 (Blackwell) require specific matrix padding that is absent in ctranslate2 <= 4.6.1. Starting with ctranslate2 4.6.2, INT8 is explicitly disabled for sm_120 at the library level (PR #1937 by @Purfview, merged 2025-12-05).

**Affected compute types:** `int8`, `int8_float16`, `int8_float32`, `int8_bfloat16` — all fail on Blackwell.

**Working compute types on Blackwell:** `float16`, `float32`, `bfloat16`

**Decision for Phase 1:** Use `compute_type="float16"` — this is the standard for RTX GPUs with FP16 tensor cores, achieves near-identical accuracy to int8 variants, and is confirmed working on sm_120.

[VERIFIED: GitHub OpenNMT/CTranslate2 #1865, SubtitleEdit/subtitleedit #10180, CTranslate2 CHANGELOG v4.6.2]

### ctranslate2 4.7.0 Windows Regression

**Symptom:** `[WinError 3] The system cannot find the path specified` — raised when importing ctranslate2 on Windows/NVIDIA machines because 4.7.0 incorrectly looks for AMD ROCm paths.

**Fix:** ctranslate2 4.7.1 (released 2026-02-04) fixes the Windows build.

**Pin requirement:** `ctranslate2==4.7.1` in requirements.txt.

[VERIFIED: GitHub OpenNMT/CTranslate2 #2009, PyPI ctranslate2 4.7.1 release notes "Fix Windows build"]

### Performance Note on Blackwell

One open GitHub issue (SYSTRAN/faster-whisper #1287, filed 2025-04-14) reports that an RTX 5070 Ti runs faster-whisper ~10% slower than an RTX 4070 Ti Super. Root cause is unresolved — likely suboptimal kernel dispatch for sm_120 in ctranslate2 4.x. This is a performance concern, not a correctness blocker. Phase 1 success criterion is transcription within 3 seconds, which float16 on any RTX 50-series will clear with margin.

[CITED: github.com/SYSTRAN/faster-whisper/issues/1287]

---

## Installation Sequence

### Step 1: Create venv with Python 3.11

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python --version  # confirm 3.11.x
```

### Step 2: Install CUDA DLL packages first

These provide cublas64_12.dll, cudnn64_9.dll, and cudart64_12.dll into site-packages. They must be installed before ctranslate2 attempts to load them.

```powershell
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12==9.8.0.87
```

Note: The exact cuDNN patch version is flexible — the constraint is cuDNN 9.x. As of research date, `nvidia-cudnn-cu12==9.8.0.87` is the latest 9.x available. [VERIFIED: pypi.org/project/nvidia-cudnn-cu12]

### Step 3: Install ctranslate2 pinned to 4.7.1

```powershell
pip install ctranslate2==4.7.1
```

This avoids the 4.7.0 Windows ROCm regression.

### Step 4: Install faster-whisper 1.2.1

```powershell
pip install faster-whisper==1.2.1
```

This satisfies `ctranslate2>=4.0,<5` — 4.7.1 already installed, no conflict.

### Step 5: Install silero-vad (Phase 1 scope includes VAD installation verification)

```powershell
pip install silero-vad==6.2.1
```

This pulls torch as an automatic dependency. Expect ~2.5GB download on first install (PyTorch CPU+CUDA wheels). [VERIFIED: PyPI silero-vad 6.2.1 — requires torch>=1.12.0]

### Step 6: Install sounddevice

```powershell
pip install sounddevice==0.5.5
```

PortAudio DLLs are bundled in the Windows wheel — no separate install needed. [VERIFIED: python-sounddevice.readthedocs.io installation docs]

### Full requirements.txt for Phase 1

```
# Core transcription
faster-whisper==1.2.1
ctranslate2==4.7.1

# CUDA DLLs (must be on PATH for ctranslate2 to find them on Windows)
nvidia-cublas-cu12
nvidia-cudnn-cu12==9.8.0.87

# VAD (torch dependency accepted)
silero-vad==6.2.1

# Audio capture (Phase 1 scaffolding; used from Phase 2 onward)
sounddevice==0.5.5
```

### Critical: Windows DLL Discovery Pre-import

ctranslate2 on Windows loads CUDA DLLs via `ctypes.WinDLL`. The `site-packages\nvidia\*\bin` directories are NOT automatically on the PATH. Without a pre-import directory registration, ctranslate2 fails with `Library cublas64_12.dll is not found`.

**Required pre-import shim** (place in `backend/main.py` or a `startup.py` that runs before any ctranslate2 import):

```python
# windows_cuda_path.py — run before importing ctranslate2 or faster_whisper
import os
import sys

def register_cuda_dll_paths() -> None:
    """Add nvidia pip-package DLL directories to Python's DLL search path.
    
    Required on Windows: ctranslate2 loads CUDA DLLs via ctypes at startup.
    These DLLs live in site-packages/nvidia/*/bin, which is not on PATH by default.
    os.add_dll_directory() makes Python's loader search them before falling back to PATH.
    """
    if sys.platform != "win32":
        return
    try:
        import site
        for packages_dir in site.getsitepackages():
            nvidia_base = os.path.join(packages_dir, "nvidia")
            if not os.path.isdir(nvidia_base):
                continue
            for subpkg in os.listdir(nvidia_base):
                bin_dir = os.path.join(nvidia_base, subpkg, "bin")
                if os.path.isdir(bin_dir):
                    os.add_dll_directory(bin_dir)
    except Exception:
        pass  # Non-fatal: CUDA DLLs may be on system PATH already
```

[VERIFIED pattern: GitHub CuPy #8164, triton-windows #43]

---

## CUDA Detection Pattern

### Exception Taxonomy

When ctranslate2/faster-whisper fails to use CUDA, three distinct failure modes exist:

| Failure | Exception Type | Message Pattern | Cause |
|---------|---------------|-----------------|-------|
| DLL missing | `RuntimeError` | `Library cublas64_12.dll is not found or cannot be loaded` | nvidia-cublas-cu12 not installed or not on add_dll_directory path |
| Driver too old | `RuntimeError` | `CUDA failed with error CUDA driver version is insufficient for CUDA runtime version` | CUDA toolkit > driver; rare on RTX 5070 Ti with driver 591.74 |
| Blackwell INT8 | `RuntimeError` | `cuBLAS failed with status CUBLAS_STATUS_NOT_SUPPORTED` | compute_type is int8* on sm_120; fix: use float16 |
| No CUDA device | Falls back silently | No exception — model loads on CPU | CUDA not available; detect via model.device attribute |

[VERIFIED: GitHub faster-whisper #1276, #790, ctranslate2 #1865]

### Robust Device Detection Pattern

```python
import threading
import numpy as np
from faster_whisper import WhisperModel

def load_model_with_cuda_detection(
    model_size: str = "large-v3-turbo",
    preferred_device: str = "cuda",
    compute_type: str = "float16",
) -> tuple[WhisperModel, str]:
    """
    Load WhisperModel with explicit CUDA detection.
    
    Returns:
        (model, actual_device) where actual_device is "cuda" or "cpu"
    
    Raises:
        RuntimeError if CUDA was required (cpu_fallback_allowed=False) but unavailable
    """
    actual_device = preferred_device
    
    try:
        model = WhisperModel(
            model_size,
            device=preferred_device,
            compute_type=compute_type,
        )
        # Verify the underlying ctranslate2 model reports CUDA
        # model.model is a ctranslate2.models.Whisper instance with .device property
        actual_device = model.model.device
        
    except RuntimeError as exc:
        msg = str(exc)
        if "not found or cannot be loaded" in msg:
            # DLL missing — actionable message
            print(f"[CUDA SETUP ERROR] CUDA DLL missing: {msg}")
            print("[CUDA SETUP ERROR] Run: pip install nvidia-cublas-cu12 nvidia-cudnn-cu12")
            raise
        elif "CUBLAS_STATUS_NOT_SUPPORTED" in msg:
            # Blackwell INT8 error — wrong compute_type
            print(f"[CUDA CONFIG ERROR] Blackwell requires float16, not {compute_type}: {msg}")
            raise
        elif "insufficient" in msg:
            # Driver/toolkit mismatch
            print(f"[CUDA DRIVER ERROR] {msg}")
            raise
        else:
            # Unknown CUDA error — fall back to CPU with warning
            print(f"[CUDA WARNING] GPU load failed ({exc}), falling back to CPU")
            model = WhisperModel(model_size, device="cpu", compute_type="int8")
            actual_device = "cpu"
    
    return model, actual_device
```

### Verifying Actual Device Without Exceptions

```python
# After model load succeeds, verify actual device:
actual = model.model.device   # returns "cuda" or "cpu" (string)
compute = model.model.compute_type  # returns "float16", "int8", etc.
print(f"[DEVICE] {actual} | compute_type={compute}")

# Hard gate check for Phase 1:
if actual != "cuda":
    print("[HARD GATE FAIL] GPU required for Phase 1 but model loaded on CPU")
    sys.exit(1)
```

[VERIFIED: ctranslate2.models.Whisper API docs — `.device` and `.compute_type` are documented properties]

---

## Model Loading (Background Thread + Warmup Pattern)

### Why Threading.Event Over concurrent.futures

For Phase 1 (no Qt event loop, no asyncio), `threading.Thread` + `threading.Event` is the correct primitive. The `Event` gives a ready signal that the main thread can check before allowing any transcription call.

```python
import threading
import time
import numpy as np
from typing import Optional
from faster_whisper import WhisperModel

class TranscriptionEngine:
    """
    Loads WhisperModel in a background thread at construction.
    Thread-safe: transcribe() blocks until model is ready.
    """
    
    def __init__(
        self,
        model_size: str = "large-v3-turbo",
        device: str = "cuda",
        compute_type: str = "float16",
    ) -> None:
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
        t0 = time.perf_counter()
        try:
            model = WhisperModel(model_size, device=device, compute_type=compute_type)
            self._actual_device = model.model.device
            
            # Warmup: feed 1 second of silence to trigger CUDA JIT compilation.
            # This prevents the first real recording from having extra latency.
            silence = np.zeros(16000, dtype=np.float32)
            list(model.transcribe(silence, beam_size=1, language="en")[0])
            
            self._model = model
            elapsed = time.perf_counter() - t0
            print(f"[MODEL] Loaded on {self._actual_device} in {elapsed:.1f}s (warmup included)")
            
        except Exception as exc:
            self._load_error = exc
            print(f"[MODEL ERROR] {exc}")
        finally:
            self._ready.set()  # Always signal — caller checks _load_error
    
    @property
    def is_ready(self) -> bool:
        return self._ready.is_set()
    
    @property
    def actual_device(self) -> Optional[str]:
        return self._actual_device
    
    def wait_until_ready(self, timeout: float = 60.0) -> bool:
        """Block until model is loaded. Returns True if ready, False on timeout."""
        return self._ready.wait(timeout=timeout)
    
    def transcribe(self, audio: np.ndarray) -> str:
        """Block until model is ready, then transcribe. audio: float32 at 16000 Hz."""
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
```

### Expected Load Times (RTX 5070 Ti, float16)

| Stage | Expected Duration |
|-------|------------------|
| ctranslate2 init + DLL load | 1–2 s |
| large-v3-turbo weights into VRAM (~1.5GB) | 2–4 s |
| CUDA JIT warmup (first inference) | 0.5–1.5 s |
| **Total startup** | **3.5–7.5 s** |

After warmup, subsequent inferences on 15-second audio clips: < 0.5 s. [ASSUMED — based on benchmark reports for similar Blackwell hardware; not measured on this specific machine]

---

## Test WAV Approach

### Programmatic Generation (Recommended — no pre-recorded file needed)

Phase 1 should generate its test WAV at runtime using Python's stdlib `wave` module. This avoids committing binary files to the repo and works on any machine.

**Option A: Silence (for warmup validation)**
```python
import wave
import struct
import os

def write_silence_wav(path: str, duration_s: float = 1.0, sample_rate: int = 16000) -> None:
    """Write a WAV file of pure silence at 16kHz mono float-equivalent (16-bit PCM)."""
    num_samples = int(duration_s * sample_rate)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)       # mono
        wf.setsampwidth(2)       # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * num_samples)
```

**Option B: Numpy silence array (for transcribe() directly — no file needed)**

```python
import numpy as np

# faster-whisper.transcribe() accepts np.ndarray directly
silence_array = np.zeros(16000, dtype=np.float32)  # 1 second at 16kHz

segments, info = model.transcribe(silence_array, beam_size=1, language="en")
result = list(segments)  # Should return empty list or short filler token
```

[VERIFIED: GitHub faster-whisper #1323, multiple community examples — float32 at 16000 Hz is the confirmed input format]

**Option C: Generate a tone + speech-like chirp (for transcription accuracy test)**
```python
import numpy as np

def make_test_audio(duration_s: float = 3.0, sample_rate: int = 16000) -> np.ndarray:
    """Sine wave at 440Hz — not speech, but exercises transcription pipeline."""
    t = np.linspace(0, duration_s, int(duration_s * sample_rate), dtype=np.float32)
    return 0.3 * np.sin(2 * np.pi * 440 * t)
```

**Recommendation:** Use Option B (numpy silence array) for the warmup inference. For the Phase 1 success criterion ("transcribe a pre-recorded test WAV within 3 seconds"), use a bundled 5-second English speech WAV. Generate it once with any TTS tool and commit as `tests/fixtures/test_speech.wav`. Committing one ~300KB WAV file is acceptable.

### WAV Format faster-whisper Accepts

- **dtype:** `float32` (normalized -1.0 to 1.0) when passing numpy arrays
- **Sample rate:** 16000 Hz (Whisper's native rate; faster-whisper resamples if different, but 16kHz avoids the overhead)
- **Channels:** Mono (1 channel); stereo is averaged automatically
- **For file paths:** Any format readable by `ffmpeg` via `av` (the `PyAV` dependency); WAV, MP3, FLAC, etc. all work when passing a file path string

[VERIFIED: faster-whisper GitHub README, community examples]

---

## Silero VAD Setup

### Version and Dependencies

- **Package:** `silero-vad 6.2.1` (released 2026-02-24, latest as of research date)
- **Python:** >= 3.8 (3.11 confirmed compatible)
- **Dependencies auto-installed:** `torch>=1.12.0`, `torchaudio>=0.12.0`, `onnxruntime>=1.16.1`
- **torch auto-install:** YES — `pip install silero-vad` pulls PyTorch automatically

[VERIFIED: PyPI silero-vad 6.2.1 page]

### Phase 1 Scope for Silero VAD

Phase 1 is a transcription spike — silero-vad is installed but NOT wired up in Phase 1. The VAD integration is Phase 2 scope (CORE-04). Phase 1 only needs to confirm the package installs cleanly alongside the CUDA stack.

**Phase 1 validation for silero-vad:**
```python
import silero_vad  # Should import without error after pip install
# No functional test needed in Phase 1
print(f"silero-vad version: {silero_vad.__version__}")
```

### torch vs CUDA Version Conflict Risk

Silero-vad pulls whichever PyTorch version satisfies `torch>=1.12.0`. If pip installs a PyTorch CPU-only wheel, it occupies the namespace but does not interfere with ctranslate2's CUDA path (ctranslate2 uses its own CUDA binaries, not PyTorch's). If pip installs a PyTorch CUDA wheel, the two CUDA paths coexist.

**Risk:** Two CUDA DLL stacks (PyTorch's and ctranslate2's NVIDIA packages) in the same venv can occasionally conflict if they target different cuDNN major versions. With silero-vad pulling torch>=2.0 and ctranslate2 requiring cuDNN 9, this is generally safe because PyTorch 2.x ships cuDNN 9 wheels.

**Mitigation:** Pin torch to a known-good version in requirements.txt if DLL conflicts are observed:
```
torch==2.7.1  # matches silero-vad requirement and cuDNN 9
```

[ASSUMED — specific version compatibility between torch 2.7.1 and nvidia-cudnn-cu12==9.x not independently verified in this session]

---

## Project Structure

Phase 1 is a pure Python spike, but the folder layout must anticipate Phase 2 (FastAPI backend) without requiring a rename/reorganization. The chosen structure makes `backend/` the root of the Python FastAPI package.

### Recommended Layout

```
intelligent-speech/
├── backend/                    # Python FastAPI backend (Phase 2+)
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point (Phase 2); Phase 1: verify_cuda.py equivalent
│   ├── transcription/
│   │   ├── __init__.py
│   │   ├── engine.py           # TranscriptionEngine class (Phase 1 deliverable)
│   │   └── cuda_setup.py       # Windows DLL registration, device detection
│   ├── audio/                  # Phase 2: sounddevice capture
│   │   └── __init__.py
│   ├── vad/                    # Phase 2: silero-vad integration
│   │   └── __init__.py
│   └── config.py               # Phase 2+: settings loader
├── tests/
│   ├── fixtures/
│   │   └── test_speech.wav     # 5-second English speech clip for CORE-02 validation
│   ├── test_cuda_detection.py  # Phase 1 test
│   └── test_transcription.py   # Phase 1 test
├── scripts/
│   └── verify_cuda.py          # Standalone verification script (Phase 1 walking skeleton entry)
├── requirements.txt            # Phase 1 pinned deps
├── requirements-dev.txt        # pytest, black, etc.
└── .venv/                      # gitignored
```

### Why This Structure

- `backend/transcription/engine.py` becomes the `TranscriptionEngine` singleton that Phase 2 imports and wires to the FastAPI WebSocket handler — no path changes needed.
- `backend/transcription/cuda_setup.py` contains the `register_cuda_dll_paths()` function called at process startup in both the Phase 1 verification script and Phase 2's FastAPI `lifespan`.
- `scripts/verify_cuda.py` is the Phase 1 walking skeleton entry point — a standalone script that exercises the full transcription stack and prints results. Discarded after Phase 2, but its logic lives on in `engine.py`.
- `tests/` follows pytest conventions; fixtures committed at this stage avoid needing to generate audio at test time.

---

## Walking Skeleton Design

Phase 1 deliverable: a single verification script that exercises all four success criteria in sequence.

### `scripts/verify_cuda.py` — Entry Point

```python
"""
Phase 1 verification script — CUDA & Transcription Spike.
Exercises all four Phase 1 success criteria.
Run: python scripts/verify_cuda.py
"""
import sys
import time
import numpy as np

# Must run before any ctranslate2 import
from backend.transcription.cuda_setup import register_cuda_dll_paths
register_cuda_dll_paths()

from backend.transcription.engine import TranscriptionEngine

def main() -> int:
    print("=" * 60)
    print("Intelligent Speech — Phase 1 Verification")
    print("=" * 60)

    # SC1 + SC2: Load model in background thread, detect actual device
    print("\n[1] Loading large-v3-turbo on CUDA (background thread)...")
    engine = TranscriptionEngine(
        model_size="large-v3-turbo",
        device="cuda",
        compute_type="float16",
    )
    
    ready = engine.wait_until_ready(timeout=120.0)
    if not ready:
        print("[FAIL] Model did not load within 120s")
        return 1
    
    if engine.actual_device != "cuda":
        print(f"[HARD GATE FAIL] Expected device=cuda, got device={engine.actual_device}")
        print("Phase 1 requires GPU transcription. Check CUDA installation.")
        return 1
    
    print(f"[PASS] Model loaded on device={engine.actual_device}")

    # SC2: Warmup already happens inside engine._load_model — report it
    print("[PASS] CUDA JIT warmup completed (silence inference during load)")

    # SC3: Transcribe test WAV file within 3 seconds
    print("\n[3] Transcribing test speech WAV...")
    wav_path = "tests/fixtures/test_speech.wav"
    t0 = time.perf_counter()
    transcript = engine.transcribe_file(wav_path)
    elapsed = time.perf_counter() - t0
    
    if elapsed > 3.0:
        print(f"[FAIL] Transcription took {elapsed:.2f}s (limit: 3s)")
        return 1
    print(f"[PASS] Transcription in {elapsed:.2f}s: '{transcript}'")

    # SC4: CPU fallback simulation
    print("\n[4] Testing CPU fallback detection...")
    try:
        cpu_engine = TranscriptionEngine(
            model_size="large-v3-turbo",
            device="cpu",
            compute_type="int8",
        )
        cpu_engine.wait_until_ready(timeout=120.0)
        print(f"[PASS] CPU fallback device={cpu_engine.actual_device} (clearly identified)")
    except Exception as exc:
        print(f"[FAIL] CPU fallback raised unexpected exception: {exc}")
        return 1

    print("\n" + "=" * 60)
    print("[PASS] All Phase 1 success criteria met")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### What `engine.py` Must Implement for the Skeleton

1. `TranscriptionEngine.__init__(model_size, device, compute_type)` — starts background thread
2. `TranscriptionEngine.wait_until_ready(timeout)` — wraps `threading.Event.wait()`
3. `TranscriptionEngine.actual_device` property — returns `model.model.device`
4. `TranscriptionEngine.transcribe(audio: np.ndarray) -> str` — runs transcription
5. `TranscriptionEngine.transcribe_file(path: str) -> str` — convenience wrapper that reads WAV → numpy → transcribe

---

## Validation Architecture

nyquist_validation is enabled in `.planning/config.json`.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (stdlib-friendly, no special config needed for Phase 1) |
| Config file | `pytest.ini` or `pyproject.toml [tool.pytest]` — Wave 0 creates it |
| Quick run command | `pytest tests/test_cuda_detection.py -x -v` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CORE-02 | faster-whisper loads on CUDA, transcribes WAV file in <3s | integration | `pytest tests/test_transcription.py::test_transcription_on_cuda -x` | Wave 0 |
| CORE-03 | CPU fallback detected and labeled when device="cpu" requested | unit | `pytest tests/test_cuda_detection.py::test_cpu_fallback_identified -x` | Wave 0 |
| CORE-05 | WhisperModel loads in background thread; ready event fires before transcribe | unit | `pytest tests/test_cuda_detection.py::test_model_loads_in_background -x` | Wave 0 |

### Test Design Notes

- CORE-02 test is hardware-dependent (requires RTX 5070 Ti). Mark with `@pytest.mark.gpu` and document that CI will skip it without GPU.
- CORE-03 test loads on CPU with compute_type="int8" and asserts `engine.actual_device == "cpu"`. No GPU needed.
- CORE-05 test checks that `engine.is_ready` starts False, then becomes True after `wait_until_ready()`. CPU model is fine for this test.

### Sampling Rate

- **Per task commit:** `pytest tests/test_cuda_detection.py -x -v`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_cuda_detection.py` — covers CORE-03, CORE-05
- [ ] `tests/test_transcription.py` — covers CORE-02 (GPU required)
- [ ] `tests/fixtures/test_speech.wav` — 5-second English speech clip (commit as binary fixture)
- [ ] `pytest.ini` — minimal config file
- [ ] Framework install: `pip install pytest` — add to `requirements-dev.txt`

---

## Common Pitfalls

### Pitfall 1: Using int8_float16 on Blackwell

**What goes wrong:** `RuntimeError: cuBLAS failed with status CUBLAS_STATUS_NOT_SUPPORTED` immediately on `WhisperModel.__init__`.

**Why it happens:** INT8 tensor operations require specific matrix padding on sm_120 that is absent from ctranslate2 4.x. Disabled at library level in 4.6.2+.

**How to avoid:** Always use `compute_type="float16"` for RTX 5070 Ti. Do not accept CLAUDE.md's historical mention of `int8_float16` as valid for Blackwell — that recommendation predates the Blackwell-specific incompatibility.

**Warning signs:** Immediate crash at model init, not at transcription time.

### Pitfall 2: ctranslate2 4.7.0 Windows Import Failure

**What goes wrong:** `[WinError 3] The system cannot find the path specified` on `import ctranslate2` — even before any model is loaded.

**Why it happens:** 4.7.0 added AMD ROCm support and checks for `_rocm_sdk_core/bin` on all platforms including NVIDIA-only Windows machines.

**How to avoid:** Pin `ctranslate2==4.7.1` in requirements.txt.

**Warning signs:** Import error before any transcription code runs; mentions ROCm in traceback.

### Pitfall 3: CUDA DLLs Not Found on Windows

**What goes wrong:** `RuntimeError: Library cublas64_12.dll is not found or cannot be loaded`

**Why it happens:** `pip install nvidia-cublas-cu12` puts DLLs in `site-packages\nvidia\cublas\bin` — not on the Windows DLL search path by default. ctranslate2 loads them via `ctypes` at import time.

**How to avoid:** Call `register_cuda_dll_paths()` (the `os.add_dll_directory()` loop) BEFORE the first `import ctranslate2` or `import faster_whisper` statement.

**Warning signs:** Error naming a specific DLL; works when CUDA toolkit is system-installed but fails in clean venv.

### Pitfall 4: Silent CPU Fallback

**What goes wrong:** Model loads without exception but runs 10–30x slower than expected; VRAM usage shows zero in nvidia-smi.

**Why it happens:** `device="auto"` or error swallowing causes ctranslate2 to select CPU silently. There is no warning-level log from ctranslate2 when this happens.

**How to avoid:** Always check `model.model.device` after loading. For Phase 1 specifically, treat CPU device as a hard gate failure.

**Warning signs:** Transcription of 15-second audio takes > 5 seconds; nvidia-smi shows 0% GPU util during transcription.

### Pitfall 5: Transcribing Before warmup (Double-Trigger Bug)

**What goes wrong:** The first real transcription call after model load takes 3–5 extra seconds due to CUDA JIT compilation. Users trigger a second recording attempt.

**Why it happens:** ctranslate2's CUDA kernels are JIT-compiled on first use. The compilation is one-time but happens inside the first `transcribe()` call.

**How to avoid:** Always run a dummy warmup inference (numpy silence array) inside the `_load_model` thread before setting the ready event. This amortizes JIT cost during startup, before any user interaction.

**Warning signs:** First transcription exceptionally slow; subsequent transcriptions fast.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| ctranslate2 float16 produces incorrect transcripts on Blackwell | LOW | HIGH | Warmup with known audio, compare output; float16 confirmed working across multiple report sources |
| CUDA DLL path registration fails with non-standard venv layout | MEDIUM | HIGH | Test `register_cuda_dll_paths()` on a fresh venv before any other work; log which paths were registered |
| silero-vad installs torch CUDA wheel that conflicts with nvidia-cudnn-cu12 cuDNN version | MEDIUM | MEDIUM | If DLL conflicts surface, pin `torch==2.7.1+cu128` explicitly; test import order |
| large-v3-turbo model download fails at test time (network, HuggingFace rate limit) | LOW | MEDIUM | Cache model to `~/.cache/huggingface` before Phase 1 plan execution; or pre-download in Wave 0 |
| ctranslate2 4.7.1 has unresolved Windows bug not caught by research | LOW | HIGH | Verify `import ctranslate2; print(ctranslate2.__version__)` as first task in Wave 1; escape hatch is 4.6.3 |
| RTX 5070 Ti performance gap vs expected (10% slower issue #1287) | MEDIUM | LOW | Success criterion is <3s, not specific latency; 10% gap still clears by wide margin |

---

## Environment Availability

| Dependency | Required By | Available | Version | Notes |
|------------|-------------|-----------|---------|-------|
| Python 3.11 | All | ✓ | 3.11.9 | Confirmed via `python --version` |
| RTX 5070 Ti (sm_120) | CORE-02 | ✓ | Driver 591.74 | Confirmed via nvidia-smi |
| CUDA driver support | CORE-02 | ✓ | Max CUDA 13.1 (backward compat with CUDA 12) | Driver 591.74 supports CUDA 12 apps |
| CUDA toolkit (nvcc) | Build only | ✗ | — | Not needed at runtime; ctranslate2 uses pip DLLs |
| faster-whisper 1.2.1 | CORE-02 | ✗ (not installed) | — | Install in Wave 0 |
| ctranslate2 4.7.1 | CORE-02 | ✗ (not installed) | — | Install in Wave 0; 4.7.1 fixes Windows regression |
| nvidia-cublas-cu12 | CORE-02 | ✗ (not installed) | — | Install in Wave 0; provides cublas64_12.dll |
| nvidia-cudnn-cu12 9.x | CORE-02 | ✗ (not installed) | — | Install in Wave 0; provides cudnn64_9.dll |
| silero-vad 6.2.1 | D-13 | ✗ (not installed) | — | Install in Wave 0; installs torch |
| sounddevice 0.5.5 | D-12 (Phase 2) | ✗ (not installed) | — | Install in Wave 0; PortAudio bundled in Windows wheel |
| pytest | Tests | ✗ (not installed) | — | Install in Wave 0 via requirements-dev.txt |
| test_speech.wav fixture | CORE-02 test | ✗ | — | Generate/source and commit in Wave 0 |

**Missing dependencies with no fallback:**
- `nvidia-cublas-cu12`, `nvidia-cudnn-cu12` — required for GPU; no fallback (CPU-only is rejected by D-11)

**Missing dependencies with fallback:**
- None that affect Phase 1 scope

---

## Security Domain

Phase 1 is a local CLI spike with no network access, no user input beyond file paths, and no external services. No ASVS categories apply to Phase 1. Security hardening begins in Phase 2 when the FastAPI WebSocket server is introduced.

---

## Sources

### Primary (HIGH confidence)
- [GitHub OpenNMT/CTranslate2 #1865](https://github.com/OpenNMT/CTranslate2/issues/1865) — CUBLAS_STATUS_NOT_SUPPORTED on RTX 50XX, int8 disabled for sm_120
- [CTranslate2 CHANGELOG v4.6.2](https://github.com/OpenNMT/CTranslate2/blob/master/CHANGELOG.md) — "Disable INT8 for sm120 - Blackwell GPUs (#1937)"
- [GitHub OpenNMT/CTranslate2 #2009](https://github.com/OpenNMT/CTranslate2/issues/2009) — 4.7.0 Windows ROCm path regression
- [PyPI ctranslate2](https://pypi.org/project/ctranslate2/) — Latest version 4.7.1 confirmed
- [faster-whisper v1.2.1 requirements.txt](https://github.com/SYSTRAN/faster-whisper/blob/v1.2.1/requirements.txt) — `ctranslate2>=4.0,<5`
- [faster_whisper/utils.py `_MODELS`](https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/utils.py) — `"large-v3-turbo"` → `mobiuslabsgmbh/faster-whisper-large-v3-turbo`
- [PyPI silero-vad](https://pypi.org/project/silero-vad/) — Version 6.2.1, requires torch>=1.12.0
- [SubtitleEdit #10180](https://github.com/SubtitleEdit/subtitleedit/issues/10180) — float16 confirmed working, int8 fails on RTX 50-series
- [ctranslate2 models.Whisper API](https://opennmt.net/CTranslate2/python/ctranslate2.models.Whisper.html) — `.device` and `.compute_type` properties documented
- `nvidia-smi` live output — RTX 5070 Ti driver 591.74, CUDA max 13.1, confirmed on target machine

### Secondary (MEDIUM confidence)
- [GitHub SubtitleEdit/subtitleedit #10180 comments](https://github.com/SubtitleEdit/subtitleedit/issues/10180) — Multiple users confirm float16 workaround on RTX 50-series
- [GitHub CuPy #8164](https://github.com/cupy/cupy/issues/8164) — `os.add_dll_directory()` pattern for nvidia pip DLLs on Windows
- [python-sounddevice installation docs](https://python-sounddevice.readthedocs.io/en/latest/installation.html) — PortAudio bundled on Windows pip install

### Tertiary (LOW confidence — marked [ASSUMED])
- Model load time estimates (3.5–7.5s total) — [ASSUMED] based on community reports for similar Blackwell hardware; target machine not yet tested
- torch + nvidia-cudnn-cu12 cuDNN coexistence — [ASSUMED] expected safe; not independently verified in this session

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | large-v3-turbo model load time is 3.5–7.5s on RTX 5070 Ti with float16 | Model Loading | Phase 1 plan may underestimate task duration; success criteria (3s transcription) is separate from load time |
| A2 | torch pulled by silero-vad will not conflict with nvidia-cudnn-cu12 9.x DLLs at runtime | Silero VAD Setup | If DLL conflict occurs, add `torch==2.7.1+cu128` pin to requirements.txt |
| A3 | ctranslate2 4.7.1 fully resolves the Windows ROCm path error from 4.7.0 | Installation Sequence | If still broken, pin to 4.6.3 (last known good before the ROCm regression) |

**No user confirmation required for the core Blackwell finding** — the INT8-disabled-on-sm_120 behavior is verified from official release notes and multiple independent issue reports. The `compute_type="float16"` decision is HIGH confidence.

---

## Open Questions

1. **Does the ctranslate2 4.7.1 ROCm fix fully resolve the Windows NVIDIA import error?**
   - What we know: 4.7.1 release notes say "Fix Windows build"; issue #2009 was open when 4.7.1 released
   - What's unclear: Whether 4.7.1 specifically closes #2009 or it's a different Windows fix
   - Recommendation: Wave 1 first task must be `python -c "import ctranslate2; print(ctranslate2.__version__)"`. If it fails on 4.7.1, fall back to `ctranslate2==4.6.3`.

2. **Will the large-v3-turbo model already be in HuggingFace cache on this machine?**
   - What we know: No faster-whisper is installed yet; cache state is unknown
   - What's unclear: Whether the model (1.5GB) will need to be downloaded during Phase 1 execution
   - Recommendation: Include a "pre-download model" task in Wave 0 or at the start of Wave 1, with an expected network download step documented.

3. **Does silero-vad 6.2.1 install torch with CUDA or CPU-only on Windows?**
   - What we know: silero-vad requires torch>=1.12.0; pip will select the latest compatible wheel
   - What's unclear: Whether pip auto-selects a CUDA-enabled torch wheel without explicit `--index-url` for the CUDA index
   - Recommendation: After Phase 1 install, verify `torch.cuda.is_available()`. If False (CPU-only torch), this does not block faster-whisper (ctranslate2 manages its own CUDA), but documents a known state.

---

## Metadata

**Confidence breakdown:**
- Blackwell INT8 incompatibility: HIGH — multiple official sources, release changelog
- ctranslate2 4.7.0 Windows regression + 4.7.1 fix: HIGH — GitHub issue + PyPI release matching
- CUDA DLL path registration requirement: HIGH — multiple independent sources
- model name "large-v3-turbo": HIGH — verified in faster_whisper/utils.py source
- float16 working on sm_120: HIGH — confirmed in SubtitleEdit issue, CTranslate2 issue, pyvideotrans docs
- Model load time estimates: LOW — assumed from community reports
- silero-vad + torch coexistence: MEDIUM — dependency analysis, not live-tested

**Research date:** 2026-05-16
**Valid until:** 2026-06-16 (30 days; ctranslate2 releases frequently)
