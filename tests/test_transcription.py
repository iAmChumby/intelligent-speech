"""GPU-dependent transcription test.

Covers CORE-02: faster-whisper transcribes a WAV file on CUDA in < 3 seconds.
Requires RTX GPU hardware — skipped in cloud CI via `-m "not gpu"`.
"""
import pytest
import pathlib

FIXTURE_WAV = pathlib.Path("tests/fixtures/test_speech.wav")


@pytest.mark.gpu
def test_transcription_on_cuda():
    """CORE-02: Transcribe test WAV on CUDA device in < 3 seconds."""
    import time
    from backend.transcription.cuda_setup import register_cuda_dll_paths
    register_cuda_dll_paths()
    from backend.transcription.engine import TranscriptionEngine

    assert FIXTURE_WAV.exists(), f"Fixture missing: {FIXTURE_WAV}"

    engine = TranscriptionEngine(model_size="large-v3-turbo", device="cuda", compute_type="float16")
    assert engine.wait_until_ready(timeout=120.0)
    assert engine.actual_device == "cuda", f"Expected cuda, got {engine.actual_device}"

    t0 = time.perf_counter()
    result = engine.transcribe_file(str(FIXTURE_WAV))
    elapsed = time.perf_counter() - t0

    assert elapsed < 3.0, f"Transcription took {elapsed:.2f}s, limit is 3s"
    print(f"Transcription in {elapsed:.2f}s: '{result}'")
