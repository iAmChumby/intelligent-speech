---
phase: 01-cuda-transcription-spike
plan: 03
subsystem: infra
tags: [cuda, blackwell, verify, walking-skeleton, acceptance-gate]

# Dependency graph
requires:
  - phase: 01-01
    provides: project skeleton, dependency manifest, pytest infra, WAV fixture
  - phase: 01-02
    provides: cuda_setup.py (DLL shim), TranscriptionEngine (background load + warmup + device detection)
provides:
  - scripts/verify_cuda.py — Phase 1 Walking Skeleton entry point (4x SC coverage)
  - Hardware-verified CUDA stack on RTX 5070 Ti (Blackwell sm_120)
  - DLL registration fix: os.add_dll_directory + PATH augmentation
affects:
  - Phase 2 (FastAPI + Electron scaffold)
  - Phase 9 (PyInstaller packaging — CUDA DLL packaging pattern)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - DLL registration via os.add_dll_directory() + PATH env var augmentation
    - _load_error check mandatory after wait_until_ready()

key-files:
  created:
    - scripts/verify_cuda.py (126 lines)
  modified:
    - backend/transcription/cuda_setup.py (PATH augmentation fix)
    - scripts/verify_cuda.py (_load_error check fix)

key-decisions:
  - "os.add_dll_directory() alone is insufficient for cuBLAS runtime DLL loading — PATH must also be augmented"
  - "verify_cuda.py must check engine._load_error after wait_until_ready() before reporting PASS"

patterns-established:
  - "CUDA DLL search: register via os.add_dll_directory() AND os.environ['PATH']"
  - "Verification script: check _load_error before reporting success"

requirements-completed:
  - CORE-02
  - CORE-03
  - CORE-05

# Metrics
duration: 8min
completed: 2026-05-16
---

# Phase 01 Plan 03: Walking Skeleton & Hardware Verification Summary

**scripts/verify_cuda.py exercises all 4 Phase 1 success criteria on RTX 5070 Ti — all PASS**

## Hardware Verification Results

```
[PASS] Model loaded on device=cuda
[PASS] CUDA JIT warmup completed (silence inference during load)
[PASS] Transcription in 0.21s: '.'
[PASS] CPU fallback device=cpu (clearly identified)
[PASS] All Phase 1 success criteria met
```

Full test suite: **5 passed in 23.51s** (exit 0)

## Accomplishments
- verify_cuda.py Walking Skeleton exercises DLL registration → CUDA model load → device assertion → timed transcription (<3s) → CPU fallback detection
- Hardware confirmed: RTX 5070 Ti (Blackwell sm_120) with ctranslate2==4.7.1, compute_type=float16
- Critical bug found and fixed: os.add_dll_directory() alone insufficient for cuBLAS DLL loading; PATH augmentation required
- Critical bug found and fixed: verify_cuda.py did not check engine._load_error after wait_until_ready()

## Task Commits

1. **Task 1: Implement verify_cuda.py** — `51525e5` (feat)
2. **Task 2: Hardware verification** — `2ee08da` (fix: DLL registration + _load_error check)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] PATH augmentation for CUDA DLL loading**
- **Found during:** Task 2 (hardware verification)
- **Issue:** os.add_dll_directory() registered DLL paths but cublas64_12.dll was still not found during CUDA inference (LoadLibraryEx flags bypass AddDllDirectory)
- **Fix:** Augmented cuda_setup.py to also prepend registered paths to os.environ["PATH"]
- **Files modified:** backend/transcription/cuda_setup.py
- **Verification:** verify_cuda.py now reports all 4 PASS lines, 5/5 pytest pass
- **Committed in:** 2ee08da

**2. [Rule 1 - Bug] _load_error not checked in verify_cuda.py after wait_until_ready**
- **Found during:** Task 2 (hardware verification)
- **Issue:** verify_cuda.py reported PASS for SC1/SC2 even when warmup failed with _load_error set
- **Fix:** Added _load_error check immediately after wait_until_ready(), before reporting PASS
- **Files modified:** scripts/verify_cuda.py
- **Verification:** Script now correctly fails when _load_error is set (confirmed by first run before PATH fix)
- **Committed in:** 2ee08da

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 bug)
**Impact:** Both fixes essential for correctness on Windows/Blackwell. No scope creep.

## Issues Encountered
- cuBLAS DLL loading via os.add_dll_directory() works for import but fails at runtime inference — required PATH augmentation as secondary mechanism

## Next Phase Readiness
- Phase 1 is complete — CUDA stack verified on RTX 5070 Ti hardware
- Ready for Phase 2: FastAPI WebSocket backend + Electron shell

---
*Phase: 01-cuda-transcription-spike*
*Completed: 2026-05-16*
