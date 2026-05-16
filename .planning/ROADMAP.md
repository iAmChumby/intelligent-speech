# Roadmap: Intelligent Speech

## Overview

Nine focused phases that build the app from the hardest technical risk inward and outward to distribution. Phase 1 de-risks the CUDA dependency chain before any UI investment. Phase 2 completes the CLI pipeline end-to-end. Phase 3 isolates and proves text injection across all target apps. Phases 4-5 add the persistent overlay and global hotkey. Phases 6-7 layer in full profile management and the settings window. Phase 8 wires up the system tray and lifecycle. Phase 9 packages everything for distribution with a first-run download UX.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: CUDA & Transcription Spike** - Verify the CUDA DLL trinity, load faster-whisper, and transcribe a test clip — proves the stack on this hardware before anything else is built
- [ ] **Phase 2: CLI Audio Pipeline** - Capture mic audio, run transcription, call LLM, print result to console — a fully working speech-to-text pipeline with zero UI
- [ ] **Phase 3: Text Injection Engine** - Capture HWND at record-start, clipboard-swap inject, and Escape cancel — proven across Notepad, Chrome, VS Code, and Claude Desktop
- [ ] **Phase 4: Persistent Overlay UI** - PySide6 frameless always-on-top toolbar wired to the Phase 2 pipeline and Phase 3 injection, with hardcoded profiles
- [ ] **Phase 5: Global Hotkey** - System-wide hotkey triggers recording from any app, with user-configurable binding
- [ ] **Phase 6: Profile & Config System** - Full profile CRUD with built-in defaults, per-profile LLM toggle, and persistence to %APPDATA%
- [ ] **Phase 7: Settings Window** - Settings UI for LLM endpoint, Whisper model selection, and VAD silence timeout
- [ ] **Phase 8: System Tray & Lifecycle** - System tray icon with show/hide, quit, and optional startup-with-Windows
- [ ] **Phase 9: Polish & Distribution** - PyInstaller packaging with CUDA DLLs bundled, first-run model download UX, Windows 10/11 x64 target

## Phase Details

### Phase 1: CUDA & Transcription Spike
**Goal**: The CUDA dependency chain is verified, faster-whisper loads with GPU acceleration, and a test audio clip produces a transcript — all critical risks resolved before UI investment
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: CORE-02, CORE-03, CORE-05
**Success Criteria** (what must be TRUE):
  1. Running a verification script confirms the active compute device (CUDA or CPU) and prints it — no silent CPU fallback
  2. faster-whisper large-v3-turbo loads in a background thread; a dummy 1-second silence inference warms CUDA JIT without hanging
  3. A pre-recorded test WAV file is transcribed and the result is printed to console within 3 seconds on CUDA
  4. When CUDA is unavailable (simulated), the system falls back to CPU and the output clearly identifies the fallback device
**Plans:** 3 plans
Plans:
- [x] 01-01-PLAN.md — Project structure, requirements.txt, pytest infrastructure, test stubs, test_speech.wav fixture
- [x] 01-02-PLAN.md — cuda_setup.py (DLL registration shim) + engine.py (TranscriptionEngine), fill test stubs
- [ ] 01-03-PLAN.md — scripts/verify_cuda.py (Walking Skeleton entry point) + hardware verification checkpoint

### Phase 2: CLI Audio Pipeline
**Goal**: A full speech-to-text pipeline runs in the terminal — mic capture, Silero VAD auto-stop, faster-whisper transcription, optional LLM post-processing, and console output — with no UI whatsoever
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: CORE-01, CORE-04, LLM-01, LLM-02, LLM-03, LLM-04
**Success Criteria** (what must be TRUE):
  1. User presses Enter in the terminal to start recording; speaking is captured from the default microphone
  2. After a configurable silence period, recording stops automatically via Silero VAD
  3. The transcript is printed to console; if LLM is configured, the post-processed result is also printed
  4. LLM base URL, API key, and model are read from a config file — swapping between Ollama and OpenAI requires only a config edit, not a code change
  5. When LLM is disabled in the profile config, the raw transcript is printed with no LLM call made
  6. Console output shows two timing numbers: transcription time and LLM time (or "LLM: skipped")
**Plans**: TBD

### Phase 3: Text Injection Engine
**Goal**: Processed text is reliably injected into any focused Windows text field using clipboard-swap-paste, with HWND captured at record-start, Escape cancel support, and non-blocking failure warnings
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: INJ-01, INJ-02, INJ-03, INJ-04, INJ-05
**Success Criteria** (what must be TRUE):
  1. Text appears in the field that was focused when recording started — even after a 5-second processing delay during which the user clicks elsewhere
  2. Injection works without error in: Notepad (Win32), Chrome address bar, VS Code editor, Windows Terminal, and a Claude.ai browser tab
  3. Pressing Escape during or immediately after recording cancels the operation; no text is injected and the original clipboard content is intact
  4. When the target window is an elevated-privilege (admin) process, a non-blocking overlay notification warns the user that injection was blocked — no silent failure
  5. The original clipboard content (text) is restored after injection; a one-time warning is shown if the clipboard held non-text content (image, file)
**Plans**: TBD

### Phase 4: Persistent Overlay UI
**Goal**: A frameless always-on-top PySide6 toolbar is permanently visible across all Windows apps, wired to the full Phase 2 pipeline and Phase 3 injection, with hardcoded profiles and full recording state feedback
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: OVR-01, OVR-02, OVR-03, OVR-04, OVR-05, OVR-06
**Success Criteria** (what must be TRUE):
  1. The toolbar remains visible and on top when switching between Notepad, Chrome, VS Code, and the desktop — it never disappears behind another window
  2. The toolbar is frameless and draggable; its last screen position is remembered across app restarts
  3. The toolbar displays the active profile name and a state indicator cycling through Idle / Recording / Transcribing / Processing / Done
  4. Clicking the profile picker or record button on the toolbar does not steal focus from the previously active application
  5. The toolbar does not appear in Alt+Tab or the Windows taskbar
**Plans**: TBD
**UI hint**: yes

### Phase 5: Global Hotkey
**Goal**: A configurable system-wide hotkey triggers start/stop recording from any focused application without requiring the overlay to be clicked
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: HOT-01, HOT-02
**Success Criteria** (what must be TRUE):
  1. Pressing the default hotkey while VS Code, Chrome, or any other app is focused starts recording — the overlay reflects the Recording state
  2. Pressing the hotkey again stops recording and triggers the full pipeline to injection
  3. The user can change the hotkey binding in settings; the new binding takes effect without restarting the app
**Plans**: TBD

### Phase 6: Profile & Config System
**Goal**: Users can create, edit, and delete custom profiles; four built-in defaults ship with correct prompts and cannot be deleted; all profiles persist to %APPDATA% across restarts
**Mode:** mvp
**Depends on**: Phase 5
**Requirements**: PROF-01, PROF-02, PROF-03, PROF-04, PROF-05, PROF-06, PROF-07
**Success Criteria** (what must be TRUE):
  1. App ships with four built-in profiles (Verbatim, Grammar Fix, Full Rewrite, Bullet Points) pre-loaded with correct system prompts; they are visible in the toolbar picker immediately on first launch
  2. Built-in profiles cannot be deleted; a "Duplicate" option is available so users can start from a built-in
  3. User can create a new profile by entering a name and a custom system prompt, then immediately select and use it for recording
  4. User can edit the name or system prompt of any custom profile; changes are reflected in the toolbar picker without restarting
  5. User can delete any custom profile; the deletion is persisted — the profile does not return after restart
  6. The Verbatim profile (LLM disabled) produces output with no LLM call; Grammar Fix, Full Rewrite, and Bullet Points each produce visibly distinct LLM-processed output
**Plans**: TBD

### Phase 7: Settings Window
**Goal**: A settings window lets users configure the LLM endpoint, Whisper model size, and VAD silence timeout — changes apply on save without restarting
**Mode:** mvp
**Depends on**: Phase 6
**Requirements**: SET-01, SET-02, SET-03
**Success Criteria** (what must be TRUE):
  1. User opens settings, changes the LLM base URL from Ollama to an OpenAI endpoint and API key, saves, and the next recording uses the new endpoint without a restart
  2. User selects a different Whisper model size (e.g., base instead of large-v3-turbo); on next launch the selected model is loaded
  3. User adjusts the VAD silence timeout slider; the change affects when auto-stop fires on the next recording
**Plans**: TBD
**UI hint**: yes

### Phase 8: System Tray & Lifecycle
**Goal**: The app lives in the system tray, the toolbar can be shown or hidden from the tray, quit from the tray cleanly exits the process, and an optional startup-with-Windows toggle is available
**Mode:** mvp
**Depends on**: Phase 7
**Requirements**: SYS-01, SYS-02, SYS-03
**Success Criteria** (what must be TRUE):
  1. The app icon appears in the Windows system tray after launch; right-clicking it shows a context menu with Show/Hide Toolbar and Quit options
  2. Clicking Quit from the tray menu exits the process cleanly — no lingering Python processes in Task Manager
  3. When startup-with-Windows is enabled in settings, the app is present in the system tray automatically after the next Windows login; disabling it removes the startup entry
**Plans**: TBD

### Phase 9: Polish & Distribution
**Goal**: The app is packaged as a standalone Windows executable with CUDA DLLs bundled, a first-run model download UX guides new users, and it runs on any Windows 10/11 x64 machine with only a display driver installed
**Mode:** mvp
**Depends on**: Phase 8
**Requirements**: DIST-01, DIST-02, DIST-03
**Success Criteria** (what must be TRUE):
  1. The PyInstaller --onedir build runs and launches successfully on a clean Windows 11 VM that has only a GPU display driver installed (no CUDA toolkit, no Python)
  2. On first launch on a machine without a cached Whisper model, the app displays a progress indicator while downloading the selected model; recording is disabled until the download completes
  3. The packaged app runs on both Windows 10 and Windows 11 x64 without any additional runtime installation
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. CUDA & Transcription Spike | 0/3 | Planned | - |
| 2. CLI Audio Pipeline | 0/TBD | Not started | - |
| 3. Text Injection Engine | 0/TBD | Not started | - |
| 4. Persistent Overlay UI | 0/TBD | Not started | - |
| 5. Global Hotkey | 0/TBD | Not started | - |
| 6. Profile & Config System | 0/TBD | Not started | - |
| 7. Settings Window | 0/TBD | Not started | - |
| 8. System Tray & Lifecycle | 0/TBD | Not started | - |
| 9. Polish & Distribution | 0/TBD | Not started | - |
