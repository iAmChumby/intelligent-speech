# Pitfalls Research — Intelligent Speech

**Domain:** Windows desktop speech-to-text with local GPU transcription and LLM integration
**Researched:** 2026-05-16
**Overall confidence:** HIGH (most findings verified against GitHub issues, official docs, and real-world app reports)

---

## Critical Pitfalls

These have killed or severely stalled similar projects. Address them before writing a single line of feature code.

---

### C1: CTranslate2 / CUDA / cuDNN Version Trinity

**What goes wrong:** faster-whisper depends on ctranslate2 which depends on specific CUDA and cuDNN major versions. The three-way version constraint is strict and has broken repeatedly at ctranslate2 major releases.

| ctranslate2 | CUDA | cuDNN |
|-------------|------|-------|
| < 4.0 | 11.x or 12.x | 8.x |
| 4.0–4.4 | 12.x | 8.x |
| >= 4.5 | >= 12.3 | 9.x |

After ctranslate2 4.0.0, `cublas64_12.dll` is expected on Windows even when the installed CUDA is 11.8 — no graceful fallback, hard crash. After 4.5.0, cuDNN 8 was dropped entirely. The error messages name the missing DLL but give no guidance on which package provides it.

**Why it happens:** ctranslate2 ships its CUDA dependencies as separate pip extras (`nvidia-cublas-cu12`, `nvidia-cudnn-cu12`, etc.). On Windows, `pip install faster-whisper` does NOT automatically install these extras. The DLLs must either be present system-wide or installed explicitly.

**Consequences:** Application silently or loudly falls back to CPU, or crashes on model load with a cryptic `RuntimeError: Library X.dll is not found`. On the target RTX 5070 Ti, CUDA 12.3+ and cuDNN 9 are both required and available — but the install path is non-obvious and will confuse contributors.

**Warning signs:**
- `faster-whisper` reports `device=cpu` when `device=cuda` was requested
- `RuntimeError: Library cublas64_12.dll is not found or cannot be loaded`
- Transcription takes 10–30s on 30-second audio (CPU fallback)

**Prevention:**
1. Pin the exact ctranslate2 version in `requirements.txt` from day one (`ctranslate2>=4.5.0,<5.0`)
2. Add an explicit startup check: `WhisperModel.__init__` with `device="cuda"`, catch `RuntimeError`, log actual device, surface to UI if CPU
3. Document the exact pip extras required: `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12` alongside `faster-whisper`
4. Test CUDA detection on a clean venv before any other feature work

**Phase at risk:** Phase 1 (transcription core). Will block all GPU work if not resolved first.

---

### C2: Text Injection Focus Race Condition

**What goes wrong:** The app records audio, then sends it through transcription (0.3–2s) and LLM processing (0.5–5s). By the time the result is ready to inject, the user may have clicked somewhere else. The injection goes to the wrong window. Worse, the app must steal focus to inject — if it does this visibly, it disrupts the user; if it does it wrong, it types into the overlay itself.

**Compounding factor:** The standard approach (clipboard write + `Ctrl+V` via `SendInput`) has its own race: if another application reads or modifies the clipboard between the write and the paste, the wrong text gets injected, or the user's clipboard content is overwritten with no way to recover it.

**Why it happens:**
- The app must remember the foreground HWND at record-start, not at inject-time
- `GetForegroundWindow()` at the end of processing returns the app's own window, not the target
- `SetForegroundWindow()` is restricted on Windows — a background process cannot reliably activate another window without `AttachThreadInput` or a registered hotkey thread

**Consequences:** Text injected to wrong application, overlay typed into itself, or user's clipboard permanently overwritten.

**Warning signs:**
- Text appearing in the overlay window instead of the target
- "It works when I click fast but fails after a long recording"
- Clipboard contents replaced after dictation

**Prevention:**
1. Capture `GetForegroundWindow()` at the instant the record button is pressed (before any processing), store the HWND
2. At inject time, use `SetForegroundWindow(stored_hwnd)` — this can fail; handle failure explicitly
3. Use a 3-path injection strategy, tried in order:
   - a. `SendInput` with `KEYEVENTF_UNICODE` for the full text (works for most apps, avoids clipboard)
   - b. Clipboard write + synthetic `Ctrl+V` (faster for long text, clipboard-dependent)
   - c. UI Automation `SetValue` via `IUIAutomationValuePattern` (works for stubborn text fields)
4. Save the clipboard before writing to it; restore after paste completes (with a short delay)
5. Add a visible "injecting..." state so users don't click away while injection is in progress

**Phase at risk:** Phase 2 (text injection). The single most complex correctness problem in the project.

---

### C3: PyInstaller + CUDA DLL Hell for Distribution

**What goes wrong:** PyInstaller bundles Python + imports but does not know about CUDA DLLs loaded dynamically at runtime by ctranslate2. The packaged `.exe` runs fine on a machine with the full CUDA toolkit installed, then fails on another machine with `DLL not found`.

**Specific DLLs needed** (for ctranslate2 >= 4.5 with cuDNN 9):
- `cublas64_12.dll` / `cublasLt64_12.dll`
- `cudnn64_9.dll` and cuDNN sub-DLLs
- `cudart64_12.dll`
- `nvrtc64_120.dll` (sometimes)

These are 300–800 MB combined. They cannot be discovered by PyInstaller's static analysis.

**Why it happens:** ctranslate2 uses `ctypes` / `cffi` to load CUDA DLLs by name at runtime. PyInstaller sees no import statement, so it bundles nothing. The whisper-standalone-win project solved this by shipping all NVIDIA DLLs in a side-by-side archive.

**Consequences:** Packaged app is useless for distribution unless the user already has the exact CUDA toolkit version installed globally — negating the point of packaging.

**Warning signs:**
- App works in the dev venv, crashes from the PyInstaller `.exe`
- Error only happens on machines without NVIDIA developer tools
- `ctranslate2` imports successfully but GPU not detected

**Prevention:**
1. Add all CUDA DLLs explicitly to the PyInstaller spec `binaries` list — this is manual but the only reliable approach
2. Source the DLLs from the NVIDIA pip packages (`nvidia-cublas-cu12`, `nvidia-cudnn-cu12`) which install them to `site-packages` — locate them with `importlib.resources` or hardcoded paths
3. Use a `--collect-binaries ctranslate2` hook in the spec file
4. Consider an alternative: ship the app without CUDA DLLs and have an installer step that pulls the NVIDIA pip packages at install time (avoids bundling 500+ MB)
5. Test the packaged `.exe` on a clean Windows 11 VM with only the display driver (no CUDA toolkit) before every release

**Phase at risk:** Distribution phase (late). Build the packaging pipeline early to avoid discovering this at release time.

---

### C4: UIPI — Elevated Target Applications Block Injection

**What goes wrong:** Windows User Interface Privilege Isolation (UIPI) silently drops `SendInput` calls when the target window runs at a higher integrity level than the injecting process. The call returns success (`SendInput` does not set an error code for UIPI failures), but no text appears.

**Common elevated targets users will encounter:** Task Manager, Administrator-elevated terminals (Windows Terminal as Admin, cmd as Admin), system dialogs, some anticheat-protected games.

**Why it happens:** Standard Win32 applications run at Medium integrity. Programs launched as Administrator run at High integrity. `SendInput` from Medium → High is silently blocked. The API returns the number of events queued — which is still non-zero — giving no indication of failure.

**Consequences:** Silent failure that looks like a bug in the injection logic. Hard to reproduce consistently because it depends on how the user launched the target app.

**Warning signs:**
- Injection works in Notepad but not in an elevated terminal
- No error reported but text doesn't appear
- Only reproducible when the terminal was launched "as Administrator"

**Prevention:**
1. Do not run the app elevated by default — running elevated causes UAC prompt on launch, breaks always-on-top with certain game overlays, and creates other problems
2. Implement a uiAccess manifest flag (requires code signing + installation in `%ProgramFiles%`): this lets a Medium IL app send input to High IL windows
3. For the MVP: detect elevation of the target HWND using `GetProcessToken` + `GetTokenInformation(TokenIntegrityLevel)` and show a non-blocking warning in the overlay: "Target app is elevated — text injection may not work. Try running [AppName] as Administrator."
4. Document the limitation clearly in-app; do not let it surface as a silent mystery failure

**Phase at risk:** Phase 2 (text injection). Will not affect most users but will be a support headache.

---

## Moderate Risks

Real problems that require explicit design decisions, but tractable.

---

### M1: Audio Device Hot-Plug and Exclusive Mode Conflicts

**What goes wrong:** Two separate failure modes, both common:

**Mode A — Exclusive mode conflict:** Another application (game, DAW, Discord with exclusive audio) has grabbed the microphone in WASAPI Exclusive mode. The recording attempt fails with a non-descriptive PortAudio/sounddevice error. The user sees no recording activity and no clear explanation.

**Mode B — Device hot-plug stale enumeration:** `sounddevice.query_devices()` caches the device list at startup. If the user unplugs and replugs a USB headset (or connects a Bluetooth mic), the cached list is stale. Recording to the old device index either crashes or silently produces silence.

**Warning signs:**
- `sounddevice.PortAudioError: Error opening InputStream` with no further detail
- Audio recording returns empty buffers
- "It worked before I plugged in my headset"

**Prevention:**
1. Always record in WASAPI Shared mode — never request Exclusive mode; leave Exclusive to apps that need it
2. Call `sounddevice.query_devices()` fresh each time a recording session begins, not once at startup
3. Wrap all `sd.InputStream` open calls in a try/except; on failure, re-enumerate devices and retry once before surfacing an error to the UI
4. Watch for `sample rate mismatch` errors — WASAPI Shared mode requires matching the device's configured sample rate (usually 44100 or 48000 Hz); re-sample input to 16000 Hz (whisper's required rate) in Python, not at the device level
5. Show the active microphone device name in the overlay so users can see at a glance which device is selected

**Phase at risk:** Phase 1 (audio capture). Test with USB headsets and Bluetooth mics, not just the built-in mic.

---

### M2: Always-on-Top Overlay vs. Exclusive Fullscreen Games

**What goes wrong:** DirectX exclusive fullscreen (true fullscreen, not borderless windowed) bypasses the Windows compositor. `WS_EX_TOPMOST` windows cannot draw over exclusive fullscreen because those games own the output entirely. The overlay disappears or causes the game to lose focus and minimize.

**Secondary problem:** UAC dialogs run in a secure desktop (Session 0 isolation). No application window, regardless of `WS_EX_TOPMOST`, can draw over a UAC prompt.

**Warning signs:**
- Overlay visible in borderless windowed games but disappears in true fullscreen
- Game minimizes when the overlay window tries to show
- Overlay appears then immediately hides

**Prevention:**
1. For the primary use case (dictating to AI assistants), users are not in fullscreen games — this is not an MVP blocker
2. Overlay behavior in fullscreen games is a "known limitation" category: document it, don't try to fix it
3. For the UAC case: simply allow the overlay to go behind the secure desktop — do not attempt to draw over UAC (technically impossible without kernel-level code)
4. Implement a "hide during fullscreen" mode as a setting for users who do game-adjacent dictation
5. Use `RegisterShellHookWindow` or polling `GetForegroundWindow` to detect fullscreen app activation and hide the overlay proactively, avoiding the jarring minimize behavior

**Phase at risk:** Phase 1 (overlay UI). Design the overlay to be a layered `WS_EX_LAYERED | WS_EX_TOPMOST` window from day one — retrofitting this is painful.

---

### M3: Terminal Emulators and Browser Address Bars Reject SendInput

**What goes wrong:** Windows Terminal has documented bugs with `SendInput` + `KEYEVENTF_UNICODE`: newlines output in reverse order, and some Unicode characters render incorrectly when typed via synthetic keystrokes (they work fine when pasted via clipboard). Browser address bars sanitize pasted content and may strip newlines or reformat URLs. Some Electron apps (VS Code, Discord, Slack) have their own clipboard handling quirks.

**Why it happens:** Windows Terminal processes keyboard input differently from standard Win32 controls — it has its own VT input stack. Clipboard paste (`Ctrl+V`) goes through a different code path and works correctly. For browser address bars, paste triggers URL normalization.

**Warning signs:**
- Text injected correctly in Notepad but garbled in Windows Terminal
- Multiline text collapses to single line in browser address bar
- Characters appear out of order or duplicated

**Prevention:**
1. Use clipboard + `Ctrl+V` as the default injection method for long text (> ~50 characters); reserve `SendInput` char-by-char for short single-line text only
2. For terminal targets: detect window class (`CASCADIA_HOSTING_WINDOW_CLASS` for Windows Terminal, `ConsoleWindowClass` for conhost) and always use clipboard paste
3. For browser address bars: detect Chrome/Firefox/Edge window class + focused element type; warn user that multiline text will be truncated to one line
4. Test matrix: Notepad, Windows Terminal, VS Code terminal, Chrome address bar, Chrome body text, Discord, Word — cover these before declaring injection "working"

**Phase at risk:** Phase 2 (text injection). Discovery is early; mitigation is a detection-dispatch table, not a rewrite.

---

### M4: LLM API Streaming Timeout and Partial Response Handling

**What goes wrong:** Non-streaming requests to slow local models (Ollama, LM Studio) can hang for 30–120 seconds with no feedback. The UI appears frozen. If the connection drops mid-response on a streaming call, the partial text is either discarded or injected as-is (truncated mid-sentence).

**Secondary problem:** Ollama and LM Studio may return HTTP 200 with an empty body, or HTTP 200 with a partial JSON body, on timeout or memory pressure. Standard OpenAI client libraries raise exceptions on these, but the error messages are unhelpful to users.

**Warning signs:**
- UI freezes after record button is released
- Occasional injection of half-sentences
- "Works on fast models, hangs on slow ones"

**Prevention:**
1. Always run LLM calls on a background thread — never on the UI thread
2. Set explicit timeouts: connect timeout = 5s, read timeout = 60s (configurable in settings)
3. For streaming: accumulate chunks and display a live preview in the overlay ("processing...") with the partial text visible — this provides feedback and lets users cancel
4. On timeout: surface a clear "LLM timed out" error with the raw transcription still available (so the dictation isn't lost) and a "retry" / "inject raw transcript" option
5. Do not swallow connection errors — surface them with the endpoint URL so users can diagnose misconfigured Ollama/LM Studio ports

**Phase at risk:** Phase 3 (LLM integration). Design the timeout and error state before wiring up the UI.

---

### M5: first-inference Cold Start Latency (Model Loading)

**What goes wrong:** Loading the faster-whisper large-v3 model into CUDA VRAM takes 3–8 seconds on first use. The CUDA runtime itself also has a cold start. If the model is loaded lazily (on first record press), the user presses record, sees nothing for several seconds, assumes the app is broken, and presses record again — creating a double-load race.

**Why it happens:** large-v3 is ~1.5 GB of weights. CUDA kernel compilation (JIT) adds another second. Subsequent inferences after the model is warm are fast (< 0.5s for typical dictation on an RTX 5070 Ti).

**Warning signs:**
- First record takes 8+ seconds with no visual feedback
- Double-record bug: user presses record twice because nothing happened

**Prevention:**
1. Load the model at application startup in a background thread, not on first record press
2. Show a non-blocking loading indicator in the overlay ("Loading model...") during startup
3. Disable the record button until the model is ready
4. Keep the model loaded in memory for the app's lifetime — do not unload between recordings (VRAM on an RTX 5070 Ti is not a constraint)
5. Consider a dummy inference at startup (pass 1 second of silence through the model) to trigger CUDA JIT compilation before the user records for real

**Phase at risk:** Phase 1 (transcription core). The startup loading strategy must be designed before the UI, not retrofitted.

---

## Minor Gotchas

Worth knowing. Won't block you, but will bite if ignored.

---

### G1: Windows Defender SmartScreen and Antivirus False Positives

PyInstaller-packaged executables are routinely flagged as malware because PyInstaller is widely used by malware authors. Keyboard simulation (`SendInput`) further increases suspicion. Without a code-signing certificate, every user sees a SmartScreen "Unknown Publisher" warning.

**Prevention:** Budget for an EV code-signing certificate before any public distribution. Nuitka-compiled binaries trigger fewer false positives than PyInstaller bundles. Submit the packaged exe to Microsoft Security Intelligence for analysis before each release.

**Phase at risk:** Distribution. Not a development concern until packaging.

---

### G2: Clipboard Content Overwrite (User Data Loss)

The clipboard paste approach for text injection replaces whatever the user had on the clipboard. For power users who copy-paste frequently, this is a jarring data-loss experience.

**Prevention:** Before writing to clipboard, read and save the current contents. After paste completes (add a 100–200ms delay for the target app to process), restore the original clipboard content. Handle clipboard open failures gracefully (another app may have the clipboard open).

**Phase at risk:** Phase 2 (text injection).

---

### G3: SQLite Schema Migration Without a Strategy

Adding a new column (e.g., `profiles.hotkey`, `profiles.last_used`) to SQLite without a migration plan means existing user databases silently miss the column. The app crashes with `OperationalError: no such column`.

**Prevention:** Use `PRAGMA user_version` as a schema version counter from day one. On startup, run all pending migration scripts in order atomically. The implementation is 30 lines of Python — do it before shipping the first profile-storing release.

**Phase at risk:** Phase 2 (profile system). Add the migration runner before persisting any data.

---

### G4: Windows Microphone Privacy Gate

Windows 11 has a system-level microphone privacy setting (`Settings > Privacy > Microphone`). If "Let desktop apps access your microphone" is off, `sounddevice` / `pyaudio` will open the stream successfully but receive silence. No error is raised.

**Prevention:** On startup, attempt a 0.1s test recording and check if the RMS of the buffer is exactly zero. If so, attempt to detect the privacy setting via registry (`HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone`) and surface a specific "Check microphone permissions" error rather than a generic audio error.

**Phase at risk:** Phase 1 (audio capture).

---

### G5: OpenAI-Compatible APIs Are Not All Identical

Ollama, LM Studio, and Claude (via proxy) all accept OpenAI-format requests but differ in: which parameters they ignore, how they handle `system` role vs `user` role, streaming chunk format variations, and error response schemas. A profile that works with OpenAI may fail silently with a local model.

**Prevention:** Validate the LLM endpoint at profile-save time with a minimal test request. Log the raw HTTP response on errors (behind a debug flag). Do not assume `openai` Python SDK error types — catch `httpx` exceptions as well.

**Phase at risk:** Phase 3 (LLM integration).

---

### G6: Push-to-Talk Hotkey Conflicts with Games and Other Apps

A global hotkey (e.g., `mouse side button`, `F13`) registered via `RegisterHotKey` or a low-level keyboard hook will fire inside games, potentially triggering in-game actions simultaneously. Some games block low-level hooks entirely.

**Prevention:** Use `SetWindowsHookEx(WH_KEYBOARD_LL)` rather than `RegisterHotKey` — hooks can be filtered by foreground window. Allow users to configure any key/button combination. Default to a mouse side button or a key unlikely to conflict (e.g., `Pause/Break`). Document that the hotkey fires globally and advise users accordingly.

**Phase at risk:** Phase 1 (overlay UI).

---

## Phase-Risk Mapping

| Phase / Component | Primary Pitfalls | Severity |
|---|---|---|
| Phase 1: Audio capture + transcription core | C1 (CUDA version trinity), M1 (audio device), M5 (cold start), G4 (mic privacy) | Critical |
| Phase 1: Overlay UI window | M2 (fullscreen games), G6 (hotkey conflicts) | Moderate |
| Phase 2: Text injection | C2 (focus race condition), C4 (UIPI elevation), M3 (terminal/browser compat), G2 (clipboard overwrite) | Critical |
| Phase 2: Profile system | G3 (SQLite migration) | Minor (easy to fix, hard to fix later) |
| Phase 3: LLM integration | M4 (streaming timeout), G5 (API compatibility) | Moderate |
| Distribution / packaging | C3 (PyInstaller + CUDA DLLs), G1 (antivirus false positive) | Critical for distribution |

**Sequencing recommendation:** Resolve C1 (CUDA detection and version pinning) on day one before any other code. Resolve M5 (startup loading strategy) before the first UI prototype so the architecture accommodates it. Leave C3 (packaging) for a dedicated packaging spike before any external distribution — do not discover it at release.
