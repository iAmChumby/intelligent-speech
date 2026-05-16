# Research Summary - Intelligent Speech

**Synthesized:** 2026-05-16
**Sources:** STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md
**Overall confidence:** HIGH

---

## Build vs Buy Verdict

**Build from scratch.**

Eight tools were audited. None satisfies all six requirements. The blocking gap across every tool is R1: no existing product ships a persistent always-on-screen toolbar that displays the active profile and lets you switch before recording. Every tool treats the recording indicator as a transient element. The second gap is R2: no tool models a profile as a first-class (name + system prompt) entity with a visual selector -- the closest (TypeWhisper Workflows) is trigger-based, not intent-first.

TypeWhisper (Windows Beta) is the closest open-source candidate. If the persistent toolbar requirement were dropped, it would be worth a serious trial. It is not being dropped -- the toolbar is the central UX differentiator. The custom RTX 5070 Ti hardware is also a factor: no off-the-shelf tool is optimized for faster-whisper large-v3 on CUDA; building unlocks sub-500ms transcription as a first-class capability.

---

## Interim Stopgap

**SpeechPulse (~$20 one-time)** is the recommended bridge while building. It satisfies R3, R4, R5, and R6 (local Whisper + Ollama support + global injection + one-time cost). It is missing R1 (no persistent toolbar) and R2 unification, but it covers the core dictation workflow adequately for day-to-day use during development. The 30-day trial can validate fit before purchasing. Do not use SuperWhisper ($849 lifetime or $9.99/mo) as a stopgap -- the cost is not justified.

---

## Recommended Stack

| Component | Choice | Version | Key Reason |
|-----------|--------|---------|------------|
| Python | CPython | 3.11 | Sweet spot for faster-whisper, PySide6, and PyInstaller ecosystem |
| GUI framework | PySide6 | latest Qt6 | LGPL license (distributable), official Qt binding, identical API to PyQt6 |
| Transcription | faster-whisper | 1.2.1 | 4x faster than openai/whisper, native CUDA 12 support, CTranslate2-backed |
| Default model | large-v3-turbo | -- | 8x faster than large-v3 for English, ~1.5GB VRAM at int8, <2% WER delta |
| CUDA packages | nvidia-cublas-cu12 + nvidia-cudnn-cu12 | cudnn 9.x | Required by ctranslate2 >= 4.5; must be explicitly pip-installed |
| Audio capture | sounddevice | 0.5.5 | NumPy-native callbacks, clean API, pip-installable on Windows, no PyAudio friction |
| Global hotkey | pynput | 1.8.1 | GlobalHotKeys works system-wide without requiring Administrator rights |
| Text injection | pynput + pywin32 | -- | pynput for Ctrl+V SendInput; pywin32 for HWND tracking and clipboard ops |
| LLM client | openai (AsyncOpenAI) | 2.37.0 | base_url param makes it compatible with Ollama, LM Studio, OpenAI, Claude |
| Config/profiles | stdlib json | -- | Flat JSON in %APPDATA%; no SQLite needed for this data volume |
| Packaging | PyInstaller | 6.20.0 | De facto standard; --onedir mode required (never --onefile) |

---

## Key Architecture Decisions

- **PySide6 over PyQt6.** STACK.md defaulted to PyQt6 (GPL); ARCHITECTURE.md recommends PySide6 (LGPL). PySide6 wins: same Qt6 internals, zero licensing friction, official Qt binding. Use Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool from the start; Qt.Tool suppresses Alt+Tab and taskbar presence, correct for a floating overlay.

- **Sequential state machine, not concurrent pipeline.** Five states: IDLE -> RECORDING -> TRANSCRIBING -> PROCESSING -> INJECTING -> IDLE. Record button disabled during TRANSCRIBING through INJECTING. One recording at a time. Eliminates concurrency bugs and matches single-user dictation.

- **Threading model: Qt main thread + asyncio loop + ThreadPoolExecutor.** Qt event loop owns the main thread (non-negotiable). Blocking WhisperModel.transcribe() runs in a ThreadPoolExecutor via loop.run_in_executor(). LLM HTTP calls use AsyncOpenAI on the asyncio loop (I/O-bound, no thread consumed). sounddevice audio callback writes to queue.Queue; asyncio drains it. Cross-thread Qt updates use QMetaObject.invokeMethod(Qt.QueuedConnection).

- **Text injection: clipboard-swap + Ctrl+V exclusively.** Works universally across Electron apps (VS Code, Discord, Claude Desktop), Win32 native apps, browsers, and terminals. Pattern: (1) capture HWND at record-start before overlay takes focus, (2) save clipboard, (3) write polished text, (4) SetForegroundWindow(stored_hwnd), (5) synthetic Ctrl+V via pynput, (6) restore clipboard after 150ms.

- **WhisperModel loaded at startup, kept alive.** Load once in a background thread on app launch with a visible loading badge and disabled record button. Run a dummy 1-second silence inference to warm CUDA JIT. Never unload between recordings -- 1.5GB VRAM on RTX 5070 Ti is not a constraint.

- **JSON files in %APPDATA%, not SQLite.** config.json for app settings, profiles.json for user profiles. Atomic writes (write to .tmp, then os.replace()) prevent corruption. API key in config.json at MVP; migrate to Windows Credential Manager via keyring before any public release.

---

## Critical Risks (Must Address in Phase 1)

**1. CUDA trinity version lock (C1) -- Severity: Critical**
ctranslate2 >= 4.5 requires CUDA 12.3+ AND cuDNN 9. pip install faster-whisper alone does NOT install the required DLLs on Windows. Failure mode: cryptic RuntimeError (cublas64_12.dll not found) or silent CPU fallback (10-30x slower). Fix on day one: explicitly install nvidia-cublas-cu12 and nvidia-cudnn-cu12==9.0.0; add a startup device check that surfaces the actual compute device in the overlay.

**2. Text injection focus race condition (C2) -- Severity: Critical**
By the time transcription and LLM processing complete (0.8-7s), the user may have clicked elsewhere. GetForegroundWindow() at inject-time returns the overlay, not the target. Fix: capture HWND the instant the global hotkey fires, before the overlay takes focus. At inject-time, SetForegroundWindow(stored_hwnd) and handle failure explicitly -- never silently inject to the wrong window.

**3. UIPI elevation blocks injection (C4) -- Severity: Moderate, silent failure**
SendInput from a Medium-integrity process to a High-integrity (Admin-run) window is silently dropped -- the API returns success but no text appears. Fix: detect target window integrity level at inject-time; show a non-blocking overlay warning. Do not run the app elevated by default.

**4. PyInstaller + CUDA DLL hell (C3) -- Severity: Critical for distribution**
PyInstaller static analysis does not find CUDA DLLs loaded dynamically by ctranslate2. Packaged exe fails on machines without the full CUDA toolkit installed. Fix: explicitly add all CUDA DLLs to the PyInstaller spec binaries list, sourced from the nvidia pip packages. Test on a clean VM (display driver only, no CUDA toolkit) before every release. Run a packaging spike early.

**5. WhisperModel cold start (M5) -- Severity: Moderate UX**
First load of large-v3-turbo takes 3-8s with CUDA JIT compilation. If loaded lazily on first record press with no feedback, users assume the app is broken and press again, creating a double-load race. Fix: load at startup in a background thread with visible progress; disable the record button until ready.

---

## Build Order (Phases)

**Phase 1 -- Core Pipeline (CLI only)**
Audio capture (sounddevice) -> faster-whisper transcription (CUDA) -> AsyncOpenAI LLM call -> console print. No UI. Validates the entire hard-dependency chain before any UI investment. Resolves C1 and M5 by design. Deliverables: push-to-talk in terminal, CUDA device confirmed, LLM call working with configurable endpoint.

**Phase 2 -- Text Injection Engine**
Build and test injection in isolation across all target apps: Notepad, Chrome, Windows Terminal, VS Code, Claude.ai browser tab. Deliverables: HWND capture at hotkey-time, clipboard-swap-paste-restore sequence, verified working in all five targets. This phase carries the highest architectural risk (C2, C4, M3) -- problems discovered here change architecture; problems discovered in Phase 4 waste work.

**Phase 3 -- Overlay UI**
PySide6 frameless always-on-top overlay wired to the Phase 1 pipeline. Hardcoded profiles initially. Deliverables: overlay with correct window flags (no Alt+Tab entry, no taskbar entry), profile picker, record button wired to full pipeline, five status states visible (IDLE / RECORDING / TRANSCRIBING / PROCESSING / DONE).

**Phase 4 -- Profile and Config System**
Persistent profiles.json + config.json, CRUD profile editor in settings panel, LLM endpoint configuration UI. Built-in default profiles: Verbatim (no LLM call), Grammar Fix, Full Rewrite, Bullet Points.

**Phase 5 -- Polish and Distribution**
Error handling for all failure modes (no mic, CUDA unavailable, LLM timeout, injection failed, non-text clipboard warning), system tray icon, startup-with-Windows toggle, PyInstaller packaging spike with CUDA DLL bundling.

---

## Open Questions

- **Hotkey default.** pynput GlobalHotKeys does not require Administrator rights; the keyboard library does. Which key: F9, Pause/Break, or a mouse side button? Each has different conflict profiles with games and other apps. Needs a decision before Phase 1.

- **VAD auto-stop.** faster-whisper ships Silero VAD (vad_filter=True) which trims silence and reduces hallucination. Should VAD-based auto-stop be the default UX, or manual button-release? Recommendation: manual stop as default, VAD as opt-in setting.

- **Verbatim mode.** Confirm llm_enabled: bool is a first-class profile flag, and that Verbatim is a built-in default profile. This is the fastest path: sub-500ms end-to-end on RTX 5070 Ti.

- **Clipboard restore for non-text content.** The save/restore strategy only recovers text-type clipboard data. Image or file clipboard contents will be lost. Document as a known limitation with a visible one-time warning.

- **Model download UX.** large-v3-turbo is ~1.5GB. First-run download needs a progress indicator and integrity check. Built-in downloader or external setup step? Affects Phase 1 scope.

---

## Conflicts to Resolve

**PyQt6 vs PySide6 -- RESOLVED: Use PySide6.**

STACK.md recommended PyQt6 (GPL3). ARCHITECTURE.md recommended PySide6 (LGPL). Both wrap identical Qt6 internals; the API difference is approximately 5% of the surface area.

PySide6 wins: LGPL removes all future distribution friction at zero cost today; it is the official Qt Company Python binding; PyQt6 requires a commercial license (~$550/year) to distribute a closed-source application.

Action: Treat PySide6 as the settled decision. Do not mix PyQt6 and PySide6 in the same virtual environment -- PyInstaller will abort the build.
