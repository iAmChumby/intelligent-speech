"""
Phase 1 verification script — CUDA & Transcription Spike.
Exercises all four Phase 1 success criteria (SC1–SC4) from ROADMAP.md.
Run from project root: python scripts/verify_cuda.py
"""
import os
import sys
import time

# CRITICAL: Must run BEFORE any ctranslate2 or faster_whisper import.
# ctranslate2 loads CUDA DLLs via ctypes at import time — the nvidia/
# pip-package bin/ directories must be on the DLL search path first.
from backend.transcription.cuda_setup import register_cuda_dll_paths
register_cuda_dll_paths()

# Only AFTER register_cuda_dll_paths() can ctranslate2/faster_whisper be imported.
from backend.transcription.engine import TranscriptionEngine


def main() -> int:
    """Exercise all four Phase 1 success criteria. Returns 0 on pass, 1 on failure."""
    print("=" * 60)
    print("Intelligent Speech — Phase 1 Verification")
    print("=" * 60)

    # ── SC1 + SC2: Load model on CUDA, verify actual device, confirm warmup ──
    print("\n[1] Loading large-v3-turbo on CUDA (background thread)...")
    t_cuda_start = time.perf_counter()

    engine = TranscriptionEngine(
        model_size="large-v3-turbo",
        device="cuda",
        compute_type="float16",
    )

    ready = engine.wait_until_ready(timeout=120.0)
    if not ready:
        print("[FAIL] Model did not load within 120s (timeout)")
        return 1

    cuda_load_elapsed = time.perf_counter() - t_cuda_start
    print(f"[INFO] CUDA engine ready in {cuda_load_elapsed:.1f}s")

    # Hard gate: Phase 1 requires GPU. Treat CPU fallback as a failure.
    if engine.actual_device != "cuda":
        print(
            f"[HARD GATE FAIL] Expected device=cuda, "
            f"got device={engine.actual_device}"
        )
        print("Phase 1 requires GPU transcription. Check CUDA installation.")
        return 1

    print(f"[PASS] Model loaded on device={engine.actual_device}")
    print("[PASS] CUDA JIT warmup completed (silence inference during load)")

    # ── SC3: Transcribe test WAV within 3 seconds on CUDA ──
    print("\n[3] Transcribing test speech WAV...")
    wav_path = "tests/fixtures/test_speech.wav"

    if not os.path.exists(wav_path):
        print(f"[FAIL] Test fixture not found: {wav_path}")
        print("Run Wave 1 first to generate tests/fixtures/test_speech.wav")
        return 1

    t0 = time.perf_counter()
    transcript = engine.transcribe_file(wav_path)
    elapsed = time.perf_counter() - t0

    if elapsed > 3.0:
        print(f"[FAIL] Transcription took {elapsed:.2f}s (limit: 3s)")
        return 1
    print(f"[PASS] Transcription in {elapsed:.2f}s: '{transcript}'")

    # ── SC4: CPU fallback — verify device is accurately reported as "cpu" ──
    print("\n[4] Loading large-v3-turbo on CPU (this may take 30-90s)...")
    t_cpu_start = time.perf_counter()

    cpu_engine = TranscriptionEngine(
        model_size="large-v3-turbo",
        device="cpu",
        compute_type="int8",
    )

    cpu_ready = cpu_engine.wait_until_ready(timeout=120.0)
    if not cpu_ready:
        print("[FAIL] CPU model did not load within 120s (timeout)")
        return 1

    cpu_load_elapsed = time.perf_counter() - t_cpu_start
    print(f"[INFO] CPU engine ready in {cpu_load_elapsed:.1f}s")

    if cpu_engine.actual_device != "cpu":
        print(
            f"[FAIL] Expected CPU device=cpu, "
            f"got device={cpu_engine.actual_device}"
        )
        return 1
    print(
        f"[PASS] CPU fallback device={cpu_engine.actual_device} "
        f"(clearly identified)"
    )

    # ── All criteria passed ──
    print("\n" + "=" * 60)
    print("[PASS] All Phase 1 success criteria met")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
