---
phase: 1
slug: cuda-transcription-spike
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-16
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pytest.ini` — Wave 0 creates it |
| **Quick run command** | `pytest tests/test_cuda_detection.py -x -v` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~15–90 seconds (GPU tests require model load: 3.5–7.5s) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_cuda_detection.py -x -v`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 90 seconds (dominated by model load warmup on first GPU test)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| cuda-dll-setup | 01 | 1 | CORE-02 | — | N/A (no network, no user input in Phase 1) | unit | `pytest tests/test_cuda_detection.py::test_cuda_dlls_registered -x -v` | ❌ W0 | ⬜ pending |
| device-detection | 01 | 1 | CORE-02, CORE-03 | — | CPU fallback clearly identified, no silent failure | unit | `pytest tests/test_cuda_detection.py::test_cuda_device_detected -x -v` | ❌ W0 | ⬜ pending |
| cpu-fallback | 01 | 1 | CORE-03 | — | CPU device identified and labeled explicitly | unit | `pytest tests/test_cuda_detection.py::test_cpu_fallback_identified -x -v` | ❌ W0 | ⬜ pending |
| background-loading | 01 | 1 | CORE-05 | — | N/A | unit | `pytest tests/test_cuda_detection.py::test_model_loads_in_background -x -v` | ❌ W0 | ⬜ pending |
| warmup-inference | 01 | 1 | CORE-05 | — | N/A | unit | `pytest tests/test_cuda_detection.py::test_warmup_completes -x -v` | ❌ W0 | ⬜ pending |
| transcription-speed | 01 | 2 | CORE-02 | — | N/A | integration (GPU) | `pytest tests/test_transcription.py::test_transcription_on_cuda -x -v -m gpu` | ❌ W0 | ⬜ pending |
| verification-script | 01 | 2 | CORE-02, CORE-03, CORE-05 | — | N/A | manual | `python scripts/verify_cuda.py` (prints PASS/FAIL for all 4 success criteria) | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pytest.ini` — minimal pytest config (`testpaths = tests`, `markers = gpu: requires RTX GPU`)
- [ ] `tests/__init__.py` — make tests a package
- [ ] `tests/test_cuda_detection.py` — stubs for CORE-02 (DLL registration), CORE-03 (CPU fallback), CORE-05 (background loading, warmup)
- [ ] `tests/test_transcription.py` — stub for CORE-02 GPU transcription (marked `@pytest.mark.gpu`)
- [ ] `tests/fixtures/test_speech.wav` — 5-second English speech WAV committed as binary fixture
- [ ] `requirements-dev.txt` — `pytest>=7.0`

*All tests can be stubbed (xfail or skip) in Wave 0; they must exist before execution begins.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CUDA DLL path shim resolves `cublas64_12.dll` at runtime | CORE-02 | Requires GPU + clean venv; not feasible in CI without GPU runner | Run `python -c "from backend.transcription.cuda_setup import register_cuda_dll_paths; register_cuda_dll_paths(); import ctranslate2; print(ctranslate2.__version__)"` — must print `4.7.1` without error |
| large-v3-turbo loads on RTX 5070 Ti in < 8s | CORE-02, CORE-05 | Hardware-specific timing | Run `python scripts/verify_cuda.py` and confirm load time reported |
| Transcription completes in < 3s on GPU | CORE-02 | Requires RTX 5070 Ti; CI has no GPU | Run `python scripts/verify_cuda.py` and confirm `[PASS] Transcription in X.XXs` with X.XX < 3.0 |
| CPU fallback message visible in console output | CORE-03 | Requires intentional CUDA disable | Run `engine = TranscriptionEngine(device="cpu", compute_type="int8"); engine.wait_until_ready(60)` — confirm `device=cpu` printed |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
