# Stack Research — Intelligent Speech

**Researched:** 2026-05-16
**Overall confidence:** HIGH (all major choices verified against PyPI, official docs, and multiple current sources)

---

## Recommended Stack

| Component | Library | Version | Rationale |
|-----------|---------|---------|-----------|
| Transcription | faster-whisper | 1.2.1 | CTranslate2-backed Whisper, 4x faster than openai/whisper, native CUDA 12 support |
| Default model | large-v3-turbo | — | 8x faster than large-v3 for English, near-identical WER, only 1.5GB VRAM at int8 |
| CUDA backend | nvidia-cublas-cu12 + nvidia-cudnn-cu12 | cudnn 9.x | Required by ctranslate2 latest; installable via pip |
| Audio capture | sounddevice | 0.5.5 | Modern PortAudio wrapper, NumPy arrays, clean API, MIT license |
| GUI framework | PyQt6 | 6.11.0 | Native QSystemTrayIcon, WindowStaysOnTopHint, FramelessWindowHint all built-in |
| Text injection | pyperclip + pynput | latest | Clipboard-paste strategy is the only reliably cross-app approach on Windows |
| Global hotkey | pynput | 1.8.1 | GlobalHotKeys supports system-wide hotkey capture across all foreground apps |
| LLM client | openai | 2.37.0 | `base_url` param supports every OpenAI-compatible endpoint (Ollama, LM Studio, Claude, etc.) |
| Packaging | PyInstaller | 6.20.0 | De facto standard, broad community support, known PyQt6 packaging patterns |
| Python version | CPython | 3.11 | Sweet spot: faster-whisper tested on 3.11, PyQt6 >=3.10, PyInstaller 3.8-3.14 |

---

## Detailed Rationale

### Transcription: faster-whisper

**Use it because:** faster-whisper is a reimplementation of Whisper using CTranslate2, achieving 4x throughput vs. the original openai/whisper at the same accuracy. It is the only Python-native Whisper implementation with first-class CUDA 12 support. On the project's RTX 5070 Ti (16GB VRAM), large-v3 at float16 should transcribe a 15-second dictation in under 500ms.

**CUDA requirements (non-negotiable):** ctranslate2 1.x requires CUDA 12 + cuDNN 9. Install via pip alongside faster-whisper:
```
pip install faster-whisper nvidia-cublas-cu12 nvidia-cudnn-cu12==9.0.0
```
Alternatively, Purfview's whisper-standalone-win archive provides the DLLs pre-bundled for Windows.

**Model choice — large-v3-turbo over large-v3:**
large-v3-turbo cuts the decoder from 32 to 4 layers (809M vs 1.55B parameters), running 8x faster with only ~2% WER increase on English. At int8_float16, it uses 1.5GB VRAM, leaving ample headroom. Use large-v3 only if multilingual accuracy on rare languages becomes a hard requirement.

**Compute type:** Use `float16` default for RTX 5070 Ti (Blackwell architecture, full FP16 tensor cores). Fall back to `int8_float16` only if VRAM contention occurs.

**Do NOT use:**
- `openai/whisper` — 4x slower, no CTranslate2 optimization
- `whisper.cpp` — excellent for CPU/cross-platform, but CUDA support is experimental and unreliable; wins on CPU, loses badly with GPU vs. faster-whisper
- `WhisperX` — adds forced alignment overhead; useful for timestamping transcripts, not needed for dictation use case
- `insanely-fast-whisper` — targets batched/server workloads, not interactive single-shot dictation

---

### Audio Capture: sounddevice

**Use it because:** sounddevice 0.5.5 returns NumPy arrays directly (the format faster-whisper accepts), has a clean blocking/callback API, and is actively maintained (January 2026 release). Zero friction integration:
```python
import sounddevice as sd
audio = sd.rec(int(duration * 44100), samplerate=44100, channels=1, dtype='float32')
sd.wait()
```

**Do NOT use:**
- `pyaudio` — wraps PortAudio at a lower level requiring manual buffer management, C extension build issues on Windows, last meaningful update 2022, PyAudio 0.2.x has persistent Windows installation friction
- `wave` + `pyaudio` combo — verbose, error-prone on Windows
- `librosa` — audio analysis library, not designed for live capture

---

### GUI Framework: PyQt6

**Use it because:** PyQt6 is the only Python GUI framework that natively provides all required primitives in one package:
- `Qt.WindowType.WindowStaysOnTopHint` — guaranteed always-on-top across all Windows Z-ordering
- `Qt.WindowType.FramelessWindowHint` — borderless overlay window
- `Qt.WidgetAttribute.WA_TranslucentBackground` — semi-transparent overlay
- `QSystemTrayIcon` — native Windows system tray icon with menu
- Mouse drag via `mousePressEvent` / `mouseMoveEvent` — draggable overlay with 5 lines of code
- Thread safety via `QThread` and `pyqtSignal` — transcription runs off-thread without freezing the UI

PyQt6 6.11.0 requires Python >=3.10 (ABI3 stable wheel: `cp310-abi3`).

**PySide6 vs PyQt6:** Both wrap identical Qt 6. PySide6 uses LGPL (more permissive for proprietary distribution); PyQt6 uses GPL3 (requires commercial license for closed-source distribution). Since this project targets personal use and is likely open source, PyQt6 is fine. If distribution becomes commercial without source-sharing, switch to PySide6 — the API is 95% identical.

**Do NOT use:**
- `tkinter` — no native always-on-top guarantee across all Windows apps, no built-in tray icon, primitive styling, will look dated
- `wxPython` — heavier, less active ecosystem for overlay-style apps, tray support requires more boilerplate
- `Electron` — requires Node.js runtime, 150MB+ distribution size, JavaScript bridge to call Python for transcription is poor architecture
- `WinForms/WPF` — requires .NET, not Python-native, abandoned if app logic is Python

---

### Text Injection: Clipboard Paste Strategy

**Use it because:** No single Win32 API works reliably across all Windows text fields. The clipboard-paste strategy is the only method that works consistently across:
- Electron-based apps (VS Code, Discord, Slack, Claude web browser)
- Win32 native apps (Notepad, Word)
- Browser text areas (Chrome, Edge, Firefox)
- Terminal emulators

**Implementation pattern:**
```python
import pyperclip
import pynput.keyboard

pyperclip.copy(final_text)
kb = pynput.keyboard.Controller()
with kb.pressed(pynput.keyboard.Key.ctrl):
    kb.press('v')
    kb.release('v')
```

**Why not alternatives:**
- `SendInput` / `pyautogui.write()` — character-by-character sending loses characters in fast apps, fails in Electron (DirectInput layer), unusable for long text
- `WM_SETTEXT` / `SendMessage` — works only for Win32 HWND controls, breaks in Electron, Chrome, web apps
- `UI Automation (UIA)` — correct architecture but requires app-specific XPath/patterns; too complex for system-wide injection without knowing the target app
- `pywinauto` — same limitation as UIA; built for app automation, not system-wide text injection

**Save-and-restore clipboard:** Before pasting, save existing clipboard contents and restore after a short delay (100-200ms). This prevents clobbering the user's clipboard.

---

### Global Hotkey: pynput

**Use it because:** pynput 1.8.1 provides `GlobalHotKeys` — a listener that captures key combos system-wide, even when the app window is not focused. This is essential for push-to-talk from any foreground application.

```python
from pynput import keyboard

def on_press():
    start_recording()

with keyboard.GlobalHotKeys({'<ctrl>+<shift>+r': on_press}):
    ...
```

**Do NOT use:**
- `keyboard` library (pip install keyboard) — requires running as Administrator on Windows for global hooks; unacceptable UX requirement
- `pyautogui` hotkey detection — polling-based, not event-driven; burns CPU

---

### LLM Client: openai SDK

**Use it because:** The openai Python SDK 2.37.0 natively supports `base_url` to point at any OpenAI-compatible endpoint. One client covers: OpenAI API, Anthropic (via proxy), Ollama (`http://localhost:11434/v1`), LM Studio (`http://localhost:1234/v1`), and any self-hosted vLLM instance.

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",  # configurable
    api_key="ollama"  # dummy key for local servers
)
```

**Do NOT use:**
- `httpx` direct — forces reinventing retry logic, streaming, error handling already provided by the SDK
- `requests` — synchronous only, no streaming support, no type hints
- `anthropic` SDK — vendor-locked, no benefit if the goal is OpenAI-compatible endpoints universally

---

### Packaging: PyInstaller

**Use it because:** PyInstaller 6.20.0 is the de facto standard for Python Windows distribution. It handles PyQt6 packaging reliably (official Qt for Python documentation covers this explicitly). The `--onedir` mode (not `--onefile`) is strongly preferred — it avoids the slow extraction startup of single-file bundles, which would compound with the faster-whisper model load time.

**Known friction points and mitigations:**
- Qt platform plugin (`qwindows.dll`) sometimes missed — add `--add-data "path/to/qt/plugins:PyQt6/Qt6/plugins"` or use the `--collect-all PyQt6` hook
- CUDA DLLs (cublas, cudnn) — must be explicitly included via `--add-binary` or placed in system PATH
- PyInstaller + CUDA is the single highest-friction packaging task; plan extra time

**Do NOT use:**
- `Nuitka` — compiles Python to C, produces faster runtime, but dramatically longer build times and significantly more complex CUDA DLL packaging; overkill for a personal utility
- `cx_Freeze` — less active maintenance, fewer community resources for PyQt6 + CUDA combo
- `--onefile` mode — 5-15 second cold start from self-extraction; unacceptable for a utility that should feel instant

---

### System Tray: PyQt6 QSystemTrayIcon

**Use it because:** QSystemTrayIcon is built into PyQt6 — no additional library needed. It supports:
- Custom icons
- Right-click context menus (show/hide overlay, settings, quit)
- Click-to-show behavior
- Windows notification balloons

This eliminates the need for `pystray` as an additional dependency when PyQt6 is already in the stack.

**Do NOT use:**
- `pystray` standalone — only necessary when not using Qt; redundant with PyQt6
- Windows Task Notification API directly via win32api — verbose, no benefit over QSystemTrayIcon

---

### Python Version: 3.11

**Use it because:**
- faster-whisper docs and setup guides use Python 3.11 as the reference environment
- PyQt6 6.x requires Python >=3.10; 3.11 is the stable, well-tested version
- PyInstaller supports 3.8-3.14 (note: 3.10.0 specifically has a bug; avoid 3.10.0 exactly)
- NumPy 2.x compatibility is confirmed on 3.11
- 3.12 introduced some breaking changes in the C extension ABI that affect a small number of native extension packages; 3.11 avoids edge cases

**Do NOT use:**
- Python 3.9 or lower — PyQt6 6.11.0 requires >=3.10
- Python 3.13 or 3.14 — too new for CUDA extension ecosystem; ctranslate2 wheels may lag

---

## Confidence Levels

| Component | Confidence | Source |
|-----------|------------|--------|
| faster-whisper 1.2.1 | HIGH | PyPI official page, GitHub SYSTRAN/faster-whisper |
| CUDA 12 + cuDNN 9 requirement | HIGH | faster-whisper GitHub README, ctranslate2 docs |
| large-v3-turbo model recommendation | HIGH | Multiple benchmarks, Hugging Face model card |
| sounddevice 0.5.5 | HIGH | PyPI official page, January 2026 release |
| PyQt6 6.11.0 | HIGH | PyPI official page, March 2026 release |
| Clipboard paste as injection strategy | HIGH | Cross-referenced against multiple speech-to-text projects using same pattern |
| pynput GlobalHotKeys | HIGH | pynput 1.8.1 docs, woteq.com Windows push-to-talk guide |
| openai SDK 2.37.0 base_url | HIGH | PyPI official page, OpenAI docs, May 2026 release |
| PyInstaller 6.20.0 | HIGH | PyPI official page, April 2026 release |
| Python 3.11 | MEDIUM | Consistent across community guides; 3.12 likely also works but less tested with CUDA stack |
| PyInstaller + CUDA DLL packaging | MEDIUM | Known to work but requires manual configuration; no single definitive guide |

---

## Version Notes

### faster-whisper + ctranslate2 CUDA Version Lock

ctranslate2 (the faster-whisper backend) has a hard dependency on specific CUDA/cuDNN versions:
- Current (>=4.5.0): CUDA 12 + cuDNN 9 only
- Downgrade to 4.4.0 if you need CUDA 12 + cuDNN 8
- Downgrade to 3.24.0 if you need CUDA 11 + cuDNN 8

The RTX 5070 Ti runs CUDA 12 natively, so this is not a blocker, but the install must explicitly install the right cuDNN version:
```
pip install nvidia-cudnn-cu12==9.0.0
```

### PyQt6 Minimum Python Version Changed

PyQt6 6.7+ requires Python 3.10 minimum. If the project ever needs to support Python 3.9, pin PyQt6 to 6.6.x. Do not mix PyQt6 and PySide6 in the same virtual environment — PyInstaller will abort the build.

### PyInstaller --onedir Required for CUDA

Do not use `--onefile` mode when packaging faster-whisper. The CUDA DLLs (cublas, cudnn) are large and the extraction on every launch would take 5-15 seconds. Use `--onedir` and distribute as a folder with an optional installer wrapper (e.g., NSIS or Inno Setup).

### openai SDK Async

The openai SDK provides both sync (`OpenAI`) and async (`AsyncOpenAI`) clients. Use `AsyncOpenAI` for the LLM call so it doesn't block the Qt event loop. Run it via `asyncio.run()` or `QThread` — do not call sync client methods from the main thread.

### Clipboard Restore Timing

After pasting via Ctrl+V, wait 200ms before restoring the original clipboard contents. Some apps (VS Code, browser inputs) read the clipboard asynchronously after the keypress event, and restoring too quickly causes a blank paste.
