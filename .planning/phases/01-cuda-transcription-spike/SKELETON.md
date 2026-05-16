---
phase: 01-cuda-transcription-spike
type: walking-skeleton
entry_point: python scripts/verify_cuda.py
green_when: "[PASS] All Phase 1 success criteria met" printed, exit code 0
hard_gate: exit code 1 if device != "cuda"
created: 2026-05-16
---

# Walking Skeleton — Phase 1: CUDA & Transcription Spike

## What the Skeleton Proves

Phase 1's Walking Skeleton is a standalone Python script (`scripts/verify_cuda.py`) that exercises the entire CUDA transcription stack end-to-end in a single run. When this script exits 0, the following are proven to work together on this specific hardware:

1. **Windows CUDA DLL discovery** — `register_cuda_dll_paths()` successfully adds `site-packages/nvidia/*/bin` directories to the Windows DLL search path via `os.add_dll_directory()` before `ctranslate2` loads its native extension
2. **Blackwell GPU inference** — `faster-whisper 1.2.1` with `ctranslate2==4.7.1` loads `large-v3-turbo` onto an RTX 5070 Ti (sm_120) using `compute_type="float16"` without raising `CUBLAS_STATUS_NOT_SUPPORTED`
3. **Background loading with warmup** — `TranscriptionEngine` loads the model in a daemon thread and runs a silence inference to warm the CUDA JIT before signaling readiness
4. **Sub-3-second transcription** — a 5-second test WAV is transcribed in under 3 seconds on GPU
5. **Explicit CPU fallback** — when `device="cpu"` is requested, `actual_device` accurately reports "cpu" with no silent misreporting

## Entry Point Command

Run from the project root with the virtual environment active:

```
python scripts/verify_cuda.py
```

## What "Green" Looks Like

When the skeleton is fully green, the console output contains these exact lines (in order):

```
============================================================
Intelligent Speech — Phase 1 Verification
============================================================

[1] Loading large-v3-turbo on CUDA (background thread)...
[MODEL] Loaded on cuda in X.Xs (warmup included)
[PASS] Model loaded on device=cuda
[PASS] CUDA JIT warmup completed (silence inference during load)

[3] Transcribing test speech WAV...
[PASS] Transcription in X.XXs: '...'

[4] Loading large-v3-turbo on CPU (this may take 30-90s)...
[MODEL] Loaded on cpu in X.Xs (warmup included)
[PASS] CPU fallback device=cpu (clearly identified)

============================================================
[PASS] All Phase 1 success criteria met
============================================================
```

Exit code: **0**

## The Hard Gate

If the CUDA engine loads but `engine.actual_device != "cuda"`, the script prints:

```
[HARD GATE FAIL] Expected device=cuda, got device=cpu
Phase 1 requires GPU transcription. Check CUDA installation.
```

Exit code: **1**

This gate exists because Phase 1's primary goal is proving the GPU stack works on Blackwell hardware. A silent CPU fallback (ctranslate2 downgrading to CPU without error) would give a false green — the hard gate prevents that.

## Architectural Decisions Established by This Skeleton

These decisions are locked by Phase 1 and carry forward to all subsequent phases without renegotiation:

| Decision | Value | Rationale |
|----------|-------|-----------|
| Transcription library | faster-whisper 1.2.1 | CTranslate2-backed, 4x faster than openai/whisper |
| ctranslate2 version | 4.7.1 (pinned) | 4.7.0 has Windows ROCm path regression ([WinError 3]) |
| CUDA DLL source | nvidia-cublas-cu12 + nvidia-cudnn-cu12==9.8.0.87 | pip-installable; placed in site-packages/nvidia/*/bin |
| Blackwell compute type | float16 | INT8 is disabled for sm_120 in ctranslate2 >= 4.6.2; float16 confirmed working |
| DLL registration strategy | os.add_dll_directory() loop in register_cuda_dll_paths() | Must run before first ctranslate2 import on Windows |
| Model loading pattern | threading.Thread (daemon) + threading.Event | No Qt/asyncio in Phase 1; stdlib threading is the correct primitive |
| Warmup inference | numpy zeros (1s silence) passed to model.transcribe() inside load thread | Amortizes CUDA JIT cost before ready signal fires |
| CPU fallback compute type | int8 | Valid for CPU; faster on CPU than float16 |
| Backend language | Python 3.11 | Entire CUDA/faster-whisper ecosystem best-tested on 3.11 |
| Backend directory | backend/ | Phase 2 adds FastAPI; backend/ becomes the FastAPI package root |
| Model singleton | Loaded once at startup, never unloaded | VRAM not a constraint on RTX 5070 Ti; reload cost unacceptable |

## Project Directory Structure Established

```
intelligent-speech/
├── backend/
│   ├── __init__.py
│   ├── transcription/
│   │   ├── __init__.py
│   │   ├── engine.py          <- TranscriptionEngine (Phase 1 deliverable)
│   │   └── cuda_setup.py      <- register_cuda_dll_paths() shim (Phase 1 deliverable)
│   ├── audio/
│   │   └── __init__.py        <- Phase 2: sounddevice capture
│   └── vad/
│       └── __init__.py        <- Phase 2: silero-vad integration
├── tests/
│   ├── __init__.py
│   ├── fixtures/
│   │   └── test_speech.wav    <- 5-second 16kHz mono WAV fixture
│   ├── test_cuda_detection.py <- CORE-03, CORE-05 unit tests
│   └── test_transcription.py  <- CORE-02 GPU integration test
├── scripts/
│   └── verify_cuda.py         <- Phase 1 Walking Skeleton entry point
├── requirements.txt           <- Pinned production deps (ctranslate2==4.7.1)
├── requirements-dev.txt       <- pytest
└── pytest.ini                 <- testpaths, gpu marker
```

## What This Skeleton Does NOT Prove

The following are intentionally out of scope for Phase 1 and not proven by this skeleton:

- **Microphone audio capture** — sounddevice is installed but not called (Phase 2)
- **Silero VAD** — silero-vad is installed but not wired (Phase 2)
- **LLM post-processing** — not introduced until Phase 2
- **Text injection** — Phase 3
- **Electron + React frontend** — Phase 4
- **WebSocket IPC between Electron and Python** — Phase 4
- **System tray** — Phase 8
- **PyInstaller packaging with CUDA DLLs** — Phase 9

## What Subsequent Phases Inherit

- `backend/transcription/engine.TranscriptionEngine` — Phase 2 imports this class and wraps it in the FastAPI WebSocket handler. No path changes, no refactoring needed.
- `backend/transcription/cuda_setup.register_cuda_dll_paths` — Phase 2 calls this in the FastAPI `lifespan` startup hook before any model initialization.
- `tests/fixtures/test_speech.wav` — Reused by Phase 2 pipeline tests and Phase 3 injection tests.
- `requirements.txt` — Phase 2 extends this file with FastAPI, uvicorn, openai, pynput, pyperclip. The CUDA version locks defined here remain unchanged.

## Known Risks Accepted at This Stage

| Risk | Acceptance Rationale |
|------|----------------------|
| large-v3-turbo ~10% slower on RTX 5070 Ti than RTX 4070 Ti Super (GitHub issue #1287) | Success criterion is < 3s transcription, not raw throughput. 10% gap clears the criterion with margin. |
| silero-vad may pull a CPU-only torch wheel by default | Does not block faster-whisper — ctranslate2 manages its own CUDA path independently of torch. Verify with torch.cuda.is_available() post-install; if False, note it but do not block Phase 1. |
| ctranslate2 4.7.1 may not fully resolve the 4.7.0 Windows ROCm regression | Escape hatch: pin to ctranslate2==4.6.3 if import still fails on 4.7.1. First task of Wave 1 execution: python -c "import ctranslate2; print(ctranslate2.__version__)" |
