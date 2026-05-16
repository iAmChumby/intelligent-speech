<!-- GSD:project-start source:PROJECT.md -->
## Project

**Intelligent Speech**

A Windows system-wide speech-to-text application with a persistent floating overlay. You select a processing profile, record your voice, and the app transcribes it locally, sends it through an LLM with the profile's custom instructions, then injects the polished result into whatever text field is currently focused. Built for power users who dictate to AI assistants and general text fields alike.

**Core Value:** Turn raw speech into clean, intent-faithful text without manual editing — every dictated message is ready to send the moment you release the record button.

### Constraints

- **Platform**: Windows 11 only (initially)
- **Transcription**: Local-first via faster-whisper; remote fallback via configurable Whisper-compatible API endpoint
- **LLM**: Any OpenAI-compatible API (configurable base URL + optional API key) — no hard dependency on any provider
- **Cost model**: Zero mandatory per-call cost when using local models; user opts into API cost if they choose cloud
- **Research gate**: Must validate no existing tool satisfies requirements before committing to a full build
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

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
## Detailed Rationale
### Transcription: faster-whisper
- `openai/whisper` — 4x slower, no CTranslate2 optimization
- `whisper.cpp` — excellent for CPU/cross-platform, but CUDA support is experimental and unreliable; wins on CPU, loses badly with GPU vs. faster-whisper
- `WhisperX` — adds forced alignment overhead; useful for timestamping transcripts, not needed for dictation use case
- `insanely-fast-whisper` — targets batched/server workloads, not interactive single-shot dictation
### Audio Capture: sounddevice
- `pyaudio` — wraps PortAudio at a lower level requiring manual buffer management, C extension build issues on Windows, last meaningful update 2022, PyAudio 0.2.x has persistent Windows installation friction
- `wave` + `pyaudio` combo — verbose, error-prone on Windows
- `librosa` — audio analysis library, not designed for live capture
### GUI Framework: PyQt6
- `Qt.WindowType.WindowStaysOnTopHint` — guaranteed always-on-top across all Windows Z-ordering
- `Qt.WindowType.FramelessWindowHint` — borderless overlay window
- `Qt.WidgetAttribute.WA_TranslucentBackground` — semi-transparent overlay
- `QSystemTrayIcon` — native Windows system tray icon with menu
- Mouse drag via `mousePressEvent` / `mouseMoveEvent` — draggable overlay with 5 lines of code
- Thread safety via `QThread` and `pyqtSignal` — transcription runs off-thread without freezing the UI
- `tkinter` — no native always-on-top guarantee across all Windows apps, no built-in tray icon, primitive styling, will look dated
- `wxPython` — heavier, less active ecosystem for overlay-style apps, tray support requires more boilerplate
- `Electron` — requires Node.js runtime, 150MB+ distribution size, JavaScript bridge to call Python for transcription is poor architecture
- `WinForms/WPF` — requires .NET, not Python-native, abandoned if app logic is Python
### Text Injection: Clipboard Paste Strategy
- Electron-based apps (VS Code, Discord, Slack, Claude web browser)
- Win32 native apps (Notepad, Word)
- Browser text areas (Chrome, Edge, Firefox)
- Terminal emulators
- `SendInput` / `pyautogui.write()` — character-by-character sending loses characters in fast apps, fails in Electron (DirectInput layer), unusable for long text
- `WM_SETTEXT` / `SendMessage` — works only for Win32 HWND controls, breaks in Electron, Chrome, web apps
- `UI Automation (UIA)` — correct architecture but requires app-specific XPath/patterns; too complex for system-wide injection without knowing the target app
- `pywinauto` — same limitation as UIA; built for app automation, not system-wide text injection
### Global Hotkey: pynput
- `keyboard` library (pip install keyboard) — requires running as Administrator on Windows for global hooks; unacceptable UX requirement
- `pyautogui` hotkey detection — polling-based, not event-driven; burns CPU
### LLM Client: openai SDK
- `httpx` direct — forces reinventing retry logic, streaming, error handling already provided by the SDK
- `requests` — synchronous only, no streaming support, no type hints
- `anthropic` SDK — vendor-locked, no benefit if the goal is OpenAI-compatible endpoints universally
### Packaging: PyInstaller
- Qt platform plugin (`qwindows.dll`) sometimes missed — add `--add-data "path/to/qt/plugins:PyQt6/Qt6/plugins"` or use the `--collect-all PyQt6` hook
- CUDA DLLs (cublas, cudnn) — must be explicitly included via `--add-binary` or placed in system PATH
- PyInstaller + CUDA is the single highest-friction packaging task; plan extra time
- `Nuitka` — compiles Python to C, produces faster runtime, but dramatically longer build times and significantly more complex CUDA DLL packaging; overkill for a personal utility
- `cx_Freeze` — less active maintenance, fewer community resources for PyQt6 + CUDA combo
- `--onefile` mode — 5-15 second cold start from self-extraction; unacceptable for a utility that should feel instant
### System Tray: PyQt6 QSystemTrayIcon
- Custom icons
- Right-click context menus (show/hide overlay, settings, quit)
- Click-to-show behavior
- Windows notification balloons
- `pystray` standalone — only necessary when not using Qt; redundant with PyQt6
- Windows Task Notification API directly via win32api — verbose, no benefit over QSystemTrayIcon
### Python Version: 3.11
- faster-whisper docs and setup guides use Python 3.11 as the reference environment
- PyQt6 6.x requires Python >=3.10; 3.11 is the stable, well-tested version
- PyInstaller supports 3.8-3.14 (note: 3.10.0 specifically has a bug; avoid 3.10.0 exactly)
- NumPy 2.x compatibility is confirmed on 3.11
- 3.12 introduced some breaking changes in the C extension ABI that affect a small number of native extension packages; 3.11 avoids edge cases
- Python 3.9 or lower — PyQt6 6.11.0 requires >=3.10
- Python 3.13 or 3.14 — too new for CUDA extension ecosystem; ctranslate2 wheels may lag
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
## Version Notes
### faster-whisper + ctranslate2 CUDA Version Lock
- Current (>=4.5.0): CUDA 12 + cuDNN 9 only
- Downgrade to 4.4.0 if you need CUDA 12 + cuDNN 8
- Downgrade to 3.24.0 if you need CUDA 11 + cuDNN 8
### PyQt6 Minimum Python Version Changed
### PyInstaller --onedir Required for CUDA
### openai SDK Async
### Clipboard Restore Timing
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
