---
phase: 01-cuda-transcription-spike
plan: 01
subsystem: infra
tags: [pytest, ctranslate2, faster-whisper, cuda, blackwell, ci]

# Dependency graph
requires: []
provides:
  - Pinned dependency manifest (ctranslate2==4.7.1, nvidia-cudnn-cu12==9.8.0.87, float16 default)
  - Project directory tree matching RESEARCH.md layout
  - pytest infrastructure with 5 xfail test stubs for CORE-02/03/05
  - 5-second 16kHz mono WAV fixture for transcription tests
  - GitHub Actions CI: cloud (windows-latest, non-GPU) and GPU (self-hosted RTX 5070 Ti)
affects:
  - 01-02-PLAN.md (engine.py + cuda_setup.py implementers)
  - 01-03-PLAN.md (verify_cuda.py + hardware verification)

# Tech tracking
tech-stack:
  added:
    - ctranslate2==4.7.1 (pinned to avoid 4.7.0 Windows ROCm regression)
    - faster-whisper==1.2.1
    - nvidia-cublas-cu12 (unpinned, latest cuBLAS 12)
    - nvidia-cudnn-cu12==9.8.0.87 (cuDNN 9 for Blackwell)
    - silero-vad==6.2.1
    - sounddevice==0.5.5
    - pytest>=7.0
  patterns:
    - Empty __init__.py package markers for backend/ package tree
    - .gitkeep files for empty directories (scripts/, tests/fixtures/)
    - xfail test stubs with strict=False as placeholder pattern for unimplemented code
    - CUDA DLLs installed BEFORE ctranslate2 in CI (install order critical on Windows)

key-files:
  created:
    - requirements.txt (pinned deps, no int8)
    - requirements-dev.txt (pytest>=7.0)
    - pytest.ini (testpaths=tests, gpu marker)
    - backend/__init__.py, backend/transcription/__init__.py, backend/audio/__init__.py, backend/vad/__init__.py
    - scripts/.gitkeep
    - tests/__init__.py, tests/fixtures/.gitkeep
    - tests/test_cuda_detection.py (4 xfail stubs: CORE-02/03/05)
    - tests/test_transcription.py (1 xfail GPU stub: CORE-02)
    - tests/fixtures/test_speech.wav (16kHz mono 5s sine wave)
    - .gitignore (Python, venv, models/, IDE, OS)
    - .github/workflows/ci-cloud.yml (windows-latest, non-GPU)
    - .github/workflows/ci-gpu.yml (self-hosted RTX 5070 Ti gate)
  modified: []

key-decisions:
  - "ctranslate2 pinned to 4.7.1 (avoiding 4.7.0 Windows ROCm regression #2009)"
  - "compute_type=float16 implied for Blackwell (no int8 variants anywhere in Phase 1)"
  - "CUDA DLL install order: nvidia-cublas-cu12 + nvidia-cudnn-cu12 BEFORE ctranslate2 on Windows"
  - "Test stubs use xfail(strict=False) so they pass as expected failures until Wave 2 implementations"

requirements-completed:
  - CORE-02
  - CORE-03
  - CORE-05

# Metrics
duration: 7min
completed: 2026-05-16
---

# Phase 01 Plan 01: Project Skeleton Summary

**Blackwell-safe dependency manifest, pytest infrastructure with 5 xfail stubs, and GitHub Actions CI — foundation for Phase 1's CUDA transcription verification**

## Performance

- **Duration:** 7 min
- **Started:** 2026-05-16T06:41:40Z
- **Completed:** 2026-05-16T06:48:40Z
- **Tasks:** 3
- **Files modified:** 16 (all created)

## Accomplishments
- Pinned requirements.txt with Blackwell-safe versions: ctranslate2==4.7.1, nvidia-cudnn-cu12==9.8.0.87, compute_type=float16 by implication (no int8)
- 5 xfail test stubs covering CORE-02 (DLL registration, GPU transcription), CORE-03 (CPU fallback), CORE-05 (background loading, warmup)
- CI pipeline: cloud runner verifies non-GPU tests + import sanity; GPU runner is Phase 1 source-of-truth gate with verify_cuda.py

## Task Commits

Each task was committed atomically:

1. **Task 1: Create requirements files and project directory structure** - `df3e1de` (feat)
2. **Task 2: Create pytest infrastructure and test stubs with WAV fixture** - `a752fd1` (feat)
3. **Task 3: Initialize git and create GitHub Actions CI workflows** - `d0f5862` (feat)

## Files Created/Modified
- `requirements.txt` — Pinned deps: faster-whisper 1.2.1, ctranslate2 4.7.1, nvidia-cublas-cu12, nvidia-cudnn-cu12 9.8.0.87, silero-vad 6.2.1, sounddevice 0.5.5
- `requirements-dev.txt` — pytest>=7.0
- `pytest.ini` — testpaths=tests, gpu marker, verbose addopts
- `backend/__init__.py`, `backend/transcription/__init__.py`, `backend/audio/__init__.py`, `backend/vad/__init__.py` — Package markers
- `scripts/.gitkeep` — Placeholder for Phase 1 verification scripts
- `tests/__init__.py`, `tests/fixtures/.gitkeep` — Test package and fixture directory
- `tests/test_cuda_detection.py` — 4 xfail stubs: test_cuda_dlls_registered, test_cpu_fallback_identified, test_model_loads_in_background, test_warmup_completes
- `tests/test_transcription.py` — 1 xfail GPU stub: test_transcription_on_cuda (@pytest.mark.gpu)
- `tests/fixtures/test_speech.wav` — 16kHz mono 5s 440Hz sine wave (wave stdlib, 160KB)
- `.gitignore` — Excludes __pycache__/, .venv/, .pytest_cache/, models/, IDE/OS artifacts
- `.github/workflows/ci-cloud.yml` — Windows cloud runner, CUDA DLLs before ctranslate2, pytest -m "not gpu"
- `.github/workflows/ci-gpu.yml` — Self-hosted RTX 5070 Ti runner, full suite + verify_cuda.py gate

## Decisions Made
- Git repository already existed at project root — skipped `git init` (no deviation, just pre-existing)
- WAV fixture uses 440Hz sine wave (not real speech) — acceptable for Phase 1 since success criterion is transcription COMPLETION within 3s, not word accuracy

## Deviations from Plan

None — plan executed exactly as written. Minor adaptation: git repository already existed (initialized during project setup), so `git init` was skipped per the plan's conditional instruction.

## Issues Encountered

None. All verifications passed on first attempt.

## Known Stubs

| File | Line | Stub |
|------|------|------|
| tests/test_cuda_detection.py | 7-10 | test_cuda_dlls_registered: xfail (Wave 2: cuda_setup.py not yet implemented) |
| tests/test_cuda_detection.py | 13-17 | test_cpu_fallback_identified: xfail (Wave 2: engine.py not yet implemented) |
| tests/test_cuda_detection.py | 20-28 | test_model_loads_in_background: xfail (Wave 2: engine.py not yet implemented) |
| tests/test_cuda_detection.py | 31-39 | test_warmup_completes: xfail (Wave 2: engine.py not yet implemented) |
| tests/test_transcription.py | 8-22 | test_transcription_on_cuda: xfail (Wave 2: TranscriptionEngine not yet implemented) |

All stubs are intentional xfail placeholders per 01-01-PLAN.md design. Wave 2 (01-02-PLAN.md) implements the engine and removes xfail markers.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Wave 2 executor can immediately begin implementing `backend/transcription/cuda_setup.py` and `backend/transcription/engine.py` — all imports in test stubs reference these exact paths
- `pytest.ini` is configured and `requirements.txt` is pinned — no additional scaffold needed
- Ready for 01-02-PLAN.md

---
## Self-Check: PASSED

- All 15 key files verified on disk
- All 3 task commits verified in git log (df3e1de, a752fd1, d0f5862)
- pytest collects 5 tests, all xfail, exit code 0
- requirements.txt contains ctranslate2==4.7.1, no int8 variants

---
*Phase: 01-cuda-transcription-spike*
*Completed: 2026-05-16*
