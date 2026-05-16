import pytest

# Will be implemented in Wave 2 after backend/transcription/engine.py exists
# Each test covers a specific requirement ID from VALIDATION.md


@pytest.mark.xfail(reason="Wave 2: backend/transcription/cuda_setup.py not yet implemented", strict=False)
def test_cuda_dlls_registered():
    """CORE-02: register_cuda_dll_paths() runs without error and adds paths."""
    from backend.transcription.cuda_setup import register_cuda_dll_paths
    register_cuda_dll_paths()  # Must not raise


@pytest.mark.xfail(reason="Wave 2: backend/transcription/engine.py not yet implemented", strict=False)
def test_cpu_fallback_identified():
    """CORE-03: Engine loaded with device='cpu' reports actual_device == 'cpu'."""
    from backend.transcription.engine import TranscriptionEngine
    engine = TranscriptionEngine(model_size="large-v3-turbo", device="cpu", compute_type="int8")
    assert engine.wait_until_ready(timeout=120.0)
    assert engine.actual_device == "cpu"


@pytest.mark.xfail(reason="Wave 2: backend/transcription/engine.py not yet implemented", strict=False)
def test_model_loads_in_background():
    """CORE-05: is_ready starts False immediately after construction, then becomes True."""
    from backend.transcription.engine import TranscriptionEngine
    import threading
    engine = TranscriptionEngine(model_size="large-v3-turbo", device="cpu", compute_type="int8")
    # The loader thread runs asynchronously; ready may or may not be set immediately
    # but wait_until_ready must return True within 120s
    ready = engine.wait_until_ready(timeout=120.0)
    assert ready is True
    assert engine.actual_device is not None


@pytest.mark.xfail(reason="Wave 2: backend/transcription/engine.py not yet implemented", strict=False)
def test_warmup_completes():
    """CORE-05: No exception raised during warmup inference inside _load_model."""
    from backend.transcription.engine import TranscriptionEngine
    engine = TranscriptionEngine(model_size="large-v3-turbo", device="cpu", compute_type="int8")
    ready = engine.wait_until_ready(timeout=120.0)
    assert ready
    # If _load_error is set, warmup failed
    assert engine._load_error is None
