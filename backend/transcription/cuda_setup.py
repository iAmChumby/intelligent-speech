# Pattern verified: GitHub CuPy #8164, triton-windows #43
# ctranslate2 loads CUDA DLLs via ctypes at import time.
# site-packages/nvidia/*/bin is NOT on the Windows DLL search path by default.
# os.add_dll_directory() makes Python's loader search them before falling back to PATH.
# This file MUST be imported BEFORE any ctranslate2 or faster_whisper import.
import os
import sys
from typing import List


# Module-level registry for diagnostic logging (used by verify_cuda.py in Wave 3)
_registered_paths: List[str] = []


def register_cuda_dll_paths() -> None:
    """Add nvidia pip-package DLL directories to Python's DLL search path.

    Required on Windows: ctranslate2 loads CUDA DLLs via ctypes at startup.
    These DLLs live in site-packages/nvidia/*/bin, which is not on PATH by default.
    os.add_dll_directory() makes Python's loader search them before falling back to PATH.

    Must be called BEFORE any ``import ctranslate2`` or ``import faster_whisper``
    statement. Safe to call multiple times — subsequent calls are no-ops.

    On failure: non-fatal — CUDA DLLs may already be on the system PATH.
    All exceptions are swallowed silently.
    """
    global _registered_paths

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
                    _registered_paths.append(bin_dir)

        # os.add_dll_directory() alone is insufficient for cuBLAS runtime
        # DLL loading — ctranslate2's underlying CUDA library may resolve
        # dependencies via LoadLibraryEx with flags that bypass AddDllDirectory.
        # Augmenting PATH guarantees the DLLs are found regardless of load method.
        if _registered_paths:
            existing = os.environ.get("PATH", "")
            os.environ["PATH"] = os.pathsep.join(_registered_paths) + os.pathsep + existing
    except Exception:
        pass  # Non-fatal: CUDA DLLs may be on system PATH already


def _get_registered_nvidia_paths() -> List[str]:
    """Return the list of nvidia bin/ directories that were registered.

    Used by verify_cuda.py (Wave 3) for diagnostic logging.
    Returns a copy to prevent external mutation of the internal registry.
    """
    return list(_registered_paths)
