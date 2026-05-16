# Architecture Research — Intelligent Speech

**Domain:** Windows speech-to-text desktop app with LLM post-processing
**Researched:** 2026-05-16
**Overall confidence:** HIGH (core patterns well-established; text injection strategy is the most nuanced area)

---

## Component Map

```
┌─────────────────────────────────────────────────────────────────┐
│                        PROCESS BOUNDARY                         │
│                                                                 │
│  ┌──────────────────┐     ┌──────────────────────────────────┐  │
│  │   Overlay UI     │     │        App Core / Bus            │  │
│  │  (PySide6)       │◄───►│    (asyncio event loop)          │  │
│  │                  │     │                                  │  │
│  │ • Profile picker │     │ Signals (Qt signals or asyncio   │  │
│  │ • Record button  │     │ queues) wire everything together │  │
│  │ • Status badge   │     └──────────┬───────────────────────┘  │
│  │ • Settings panel │                │                           │
│  └──────────────────┘     ┌──────────▼───────────────────────┐  │
│                           │       Audio Engine               │  │
│                           │  (sounddevice + queue.Queue)     │  │
│                           │                                  │  │
│                           │ • Mic device selection           │  │
│                           │ • Raw PCM → numpy buffer         │  │
│                           │ • VAD silence trim (optional)    │  │
│                           └──────────┬───────────────────────┘  │
│                                      │                           │
│                           ┌──────────▼───────────────────────┐  │
│                           │     Transcription Engine          │  │
│                           │  (faster-whisper, ThreadPool)    │  │
│                           │                                  │  │
│                           │ • WhisperModel loaded at startup │  │
│                           │ • Runs in background thread      │  │
│                           │ • Accepts np.ndarray, sync API   │  │
│                           └──────────┬───────────────────────┘  │
│                                      │                           │
│                           ┌──────────▼───────────────────────┐  │
│                           │       LLM Client                  │  │
│                           │  (httpx async / openai-python)   │  │
│                           │                                  │  │
│                           │ • OpenAI-compatible endpoint     │  │
│                           │ • System prompt + transcript     │  │
│                           │ • Configurable base_url + key    │  │
│                           └──────────┬───────────────────────┘  │
│                                      │                           │
│                           ┌──────────▼───────────────────────┐  │
│                           │     Injection Engine              │  │
│                           │  (pywin32 / ctypes)              │  │
│                           │                                  │  │
│                           │ • Stores hwnd before recording   │  │
│                           │ • Clipboard-swap + SendInput paste│  │
│                           │ • Clipboard restore after paste  │  │
│                           └──────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Persistence Layer                           │   │
│  │  profiles.json + config.json (AppData\Roaming)           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Owns | Does NOT own |
|-----------|------|--------------|
| Overlay UI | Window lifecycle, profile selection, record button, status display, settings panel | Audio hardware, transcription logic |
| Audio Engine | Mic stream, PCM buffering, start/stop capture | VAD model (optional add-on), transcription |
| Transcription Engine | WhisperModel lifecycle, numpy→text | Audio capture, LLM call |
| LLM Client | HTTP call to OpenAI-compatible API, prompt construction | Profile storage, injection |
| Injection Engine | Focused window HWND tracking, clipboard-swap-paste, restore | Knowing what to inject — receives final text only |
| Persistence Layer | JSON files in AppData | Runtime state (kept in memory only) |

---

## Data Flow

```
USER ACTION: Clicks record (or holds hotkey)
     │
     ▼
[1] Overlay UI
    • Snapshots focused HWND via win32gui.GetForegroundWindow()
      BEFORE the overlay takes focus — this is the injection target
    • Sets state: RECORDING
    • Emits signal → Audio Engine: start_capture(profile_id)

     │
     ▼
[2] Audio Engine (sounddevice callback thread)
    • Opens InputStream with callback
    • Callback fires ~every 20ms: appends indata.copy() to queue.Queue
    • Main capture loop drains queue, appends chunks to bytearray buffer
    • On stop_capture signal: finalizes numpy array (float32, 16kHz)

     │ numpy array (float32, mono, 16kHz)
     ▼
[3] Transcription Engine (ThreadPoolExecutor worker thread)
    • Receives np.ndarray
    • Calls WhisperModel.transcribe(audio_array, ...)
    • transcribe() is BLOCKING — must run off main thread
    • Returns plain text string via Future / asyncio callback

     │ raw transcript string
     ▼
[4] LLM Client (asyncio coroutine, httpx async)
    • Loads active profile system prompt
    • Constructs message: [{"role":"system","content":prompt},
                           {"role":"user","content":transcript}]
    • Calls configured endpoint (AsyncOpenAI or raw httpx)
    • Awaits response — non-blocking, event loop stays live

     │ polished text string
     ▼
[5] Injection Engine
    • Saves current clipboard content (win32clipboard.GetClipboardData)
    • Sets clipboard to polished text
    • Sends Ctrl+V via SendInput to previously-snapshotted HWND
    • Restores original clipboard content after ~100ms delay
    • Emits DONE signal to UI

     │
     ▼
[6] Overlay UI
    • State → IDLE
    • Brief visual success flash
```

**Critical sequencing note:** The focused HWND must be captured in step 1 BEFORE the user clicks the record button in the overlay, because clicking the overlay shifts focus to it. Implementation: use a global keyboard hook (pynput) to trigger recording without the overlay stealing focus, OR capture HWND on the last mouse-down event before the record button focus event fires. The simpler pattern is a configurable global hotkey (e.g. F9) that keeps focus in the target window entirely.

---

## Threading Model

Python's GIL means threads don't parallelize CPU work, but this app is mostly I/O-bound (mic, network) plus one CPU-bound GPU task (Whisper). The right model is:

```
Main Thread (Qt event loop)
│
├── asyncio event loop (run in background thread via asyncio.run())
│   ├── LLM HTTP calls (async/await, non-blocking)
│   ├── UI state signals dispatched to Qt via QMetaObject.invokeMethod
│   └── Coordinates pipeline stages via asyncio.Queue
│
├── ThreadPoolExecutor worker (1 thread)
│   └── WhisperModel.transcribe() — blocking CPU/GPU call
│       Called via loop.run_in_executor(executor, transcribe_fn, audio)
│
└── sounddevice callback thread (managed by PortAudio internally)
    └── Audio callback: copies chunks into thread-safe queue.Queue
        Drained by asyncio loop via run_in_executor or asyncio.to_thread
```

**Why this model:**

- Qt requires its event loop on the main thread — non-negotiable.
- faster-whisper's `transcribe()` is synchronous and blocking. It cannot be made async. It must run in a ThreadPoolExecutor so it doesn't freeze the Qt loop or the asyncio loop.
- The LLM call is I/O-bound network wait — AsyncOpenAI (or httpx.AsyncClient) on an asyncio coroutine is the correct tool. Zero threads consumed waiting for LLM response.
- sounddevice's PortAudio callback runs on its own internal thread. The callback must be minimal — copy data, put in queue, return immediately. No processing in the callback.
- The asyncio event loop bridges the gap: `loop.run_in_executor()` wraps the blocking Whisper call so it runs off-thread while asyncio continues handling other work.

**Concurrency is always sequential for a single recording session** — no parallelism needed. One recording at a time, one transcription at a time, one LLM call at a time. A simple state machine (IDLE → RECORDING → TRANSCRIBING → PROCESSING → INJECTING → IDLE) prevents double-triggers.

**Thread-safe communication:**
- sounddevice callback → asyncio: `queue.Queue` (standard library, thread-safe)
- asyncio → Qt main thread: `QMetaObject.invokeMethod` with `Qt.QueuedConnection`
- Whisper result → asyncio: `Future` returned by `run_in_executor`

---

## Key Design Decisions

### 1. Text Injection: Clipboard-Swap + SendInput Paste (not SendKeys per-character, not UIA SetValue)

**Decision:** Write text to clipboard, send Ctrl+V via SendInput, restore original clipboard.

**Rationale:**
- Sending characters one-by-one with SendInput/SendKeys is slow, unreliable for Unicode, and can fail with auto-repeat or timing issues in fast applications.
- UIA IValueProvider.SetValue() works well for WinForms/WPF text boxes but fails silently for Electron apps (VS Code, Claude Desktop), terminals (Windows Terminal, cmd.exe), and web browser address bars.
- Clipboard + paste is the method used by every production speech input tool (Windows Voice Access, Dragon NaturallySpeaking, Talon Voice) because it works universally. Every text field that accepts user input accepts paste.
- Terminal caveat: Windows Terminal supports Ctrl+V. Older cmd.exe requires the "QuickEdit + right-click to paste" mode OR Ctrl+V if enabled in settings. Inject a newline-free result to avoid premature submission.
- Save/restore clipboard: use `win32clipboard` to save the current clipboard before overwriting it, then restore after a 150ms delay (enough time for the paste to process). This preserves the user's clipboard. Note: only restores text-type clipboard data; image/file clipboard contents will be lost — document this limitation clearly.

**Implementation:**
```python
# Pseudocode for injection
hwnd = snapshot_taken_before_recording
prev_clip = win32clipboard.get_text()       # save
win32clipboard.set_text(polished_text)      # overwrite
win32gui.SetForegroundWindow(hwnd)          # refocus target
keyboard.send("ctrl+v")                    # paste via pynput or SendInput
await asyncio.sleep(0.15)                  # wait for paste
win32clipboard.set_text(prev_clip)          # restore
```

### 2. HWND Snapshot Strategy

**Decision:** Capture the focused window HWND at the moment the global hotkey is pressed (before focus shifts to overlay).

**Rationale:** If the UI has a click-to-record button, clicking it shifts focus to the overlay. By the time injection runs, the original target HWND is gone from "foreground." The cleanest solution is a global hotkey (pynput `GlobalHotKeys`) that never shifts focus — the recording starts without the overlay being clicked. The overlay's record button can remain as a visual affordance that triggers the same code path, but the preferred interaction is keyboard-driven.

Fallback: Store the last non-overlay foreground HWND by polling `GetForegroundWindow()` every ~200ms in the background, filtering out the overlay's own HWND.

### 3. UI Framework: PySide6 (not tkinter, not Electron)

**Decision:** PySide6 (Qt6 official Python bindings).

**Rationale:**
- Qt's `Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool` combination is the correct Windows-native path for always-on-top frameless overlays. The `WS_EX_TOOLWINDOW` flag (via `Qt.Tool`) prevents the overlay from appearing in Alt+Tab.
- `Qt.Tool` flag additionally suppresses taskbar presence — correct UX for a floating overlay.
- PySide6 is LGPL-licensed (PyQt6 is GPL unless commercially licensed). For a personal tool this doesn't matter, but PySide6 is the official Qt binding and tracks Qt6 releases directly.
- tkinter is too limited for modern overlay styling (translucent backgrounds, rounded corners via `WS_EX_LAYERED`). Custom painting is awkward.
- Electron is massive overhead for a native Windows app that needs Win32 API access anyway.
- PySide6's `winId()` method exposes the raw HWND, allowing direct Win32 API calls (e.g., `SetWindowLong` for extended window styles) when Qt's flags aren't sufficient.

### 4. Profile and Config Storage: JSON in AppData (not SQLite, not registry)

**Decision:** Two flat JSON files in `%APPDATA%\IntelligentSpeech\`: `config.json` for app settings, `profiles.json` for user profiles.

**Rationale:**
- Profile data is tiny: name, system prompt string, optional model override. A list of 20 profiles with 500-character prompts is ~15KB.
- SQLite is the right choice when you need queries, joins, or concurrent writes. None of those apply here.
- JSON files are human-readable and trivially editable outside the app — useful for power users.
- `%APPDATA%` (accessible as `os.environ['APPDATA']`) is the Windows-standard per-user app data location, persists across system updates, and does not require admin rights.
- Use atomic writes (write to `.tmp`, then `os.replace()`) to avoid corruption on crash.
- `config.json` schema: `{ "llm_base_url": str, "llm_api_key": str, "llm_model": str, "whisper_model": str, "hotkey": str, "active_profile_id": str }`
- `profiles.json` schema: `{ "profiles": [{ "id": uuid, "name": str, "system_prompt": str, "created_at": iso8601 }] }`
- Sensitive data (API key): store in `config.json` for simplicity at MVP. For a production release, migrate API key to Windows Credential Manager via `keyring` library.

### 5. Audio Capture: sounddevice (not PyAudio)

**Decision:** `sounddevice` with InputStream callback pattern.

**Rationale:**
- PyAudio is a thin CFFI wrapper around PortAudio with a legacy interface. It requires a separate installer or wheel and has packaging friction on Windows.
- `sounddevice` wraps the same PortAudio but with a Pythonic API, numpy-native callback interface, and pip-installable wheels. It's the current standard for Python audio work.
- The callback pattern: `sounddevice.InputStream(callback=cb, samplerate=16000, channels=1, dtype='float32')`. The callback receives a numpy array directly — no conversion needed before passing to faster-whisper.
- Record-then-process (not streaming): accumulate all callback chunks in a `queue.Queue`, drain them when recording stops, concatenate into a single `np.ndarray`. No streaming VAD complexity needed at MVP.

### 6. WhisperModel Loading: At Startup, Kept in Memory

**Decision:** Load `WhisperModel("large-v3", device="cuda", compute_type="float16")` once at app startup and keep the instance alive.

**Rationale:**
- Model loading takes 3-8 seconds for large-v3. Loading on first use creates a bad first-impression lag.
- With 16GB VRAM (RTX 5070 Ti), large-v3 in float16 uses ~3GB. No memory pressure.
- `compute_type="float16"` on CUDA is the correct setting for RTX: faster than float32, nearly identical accuracy.
- The model instance is not thread-safe for concurrent calls, but the sequential state machine guarantees only one call at a time — no concern.

### 7. LLM Client: openai Python package (not raw httpx)

**Decision:** Use `openai` Python package configured with `base_url` and `api_key`.

**Rationale:**
- The openai package supports arbitrary `base_url`, making it compatible with Ollama, LM Studio, Jan, OpenRouter, Anthropic (via compatible proxy), and OpenAI itself.
- Use `AsyncOpenAI` for non-blocking calls on the asyncio event loop.
- The package handles retry logic, timeout, and response parsing.
- No need for raw httpx — the openai package uses httpx internally anyway.

---

## Suggested Build Order

### Phase 1 — Core Pipeline (no UI)
Build and test the audio → transcription → LLM → console output pipeline as a CLI script.

**Why first:** Validates that faster-whisper loads correctly with CUDA, that audio capture produces valid input, and that the LLM call works end-to-end. De-risks the hard technical dependencies before any UI work.

Deliverables:
- `sounddevice` push-to-talk recording loop in terminal
- faster-whisper transcription working with CUDA
- OpenAI-compatible LLM call with configurable endpoint
- Prints result to console

### Phase 2 — Injection Engine
Build and test text injection in isolation.

**Why second:** Injection is the highest-risk external dependency (Windows API behavior varies). Test it separately, across multiple targets (Notepad, browser, terminal, VS Code), before wiring it to the pipeline. Failure here changes architecture; better to know early.

Deliverables:
- Focused HWND capture
- Clipboard-swap-paste-restore sequence
- Verified working in: Notepad, Chrome, Windows Terminal, VS Code, Claude.ai browser tab

### Phase 3 — Overlay UI
Build the floating overlay with PySide6.

**Why third:** The pipeline works. Now add the UI that controls it. Start with hardcoded profiles, wire to Phase 1 pipeline, validate the full UX loop.

Deliverables:
- Frameless always-on-top overlay
- Profile picker (hardcoded at first)
- Record button / hotkey integration
- Status display (IDLE / RECORDING / PROCESSING / DONE)

### Phase 4 — Profile and Config System
Add persistence.

**Why fourth:** The pipeline and UI are validated. Now make it configurable without code changes.

Deliverables:
- `profiles.json` CRUD (create/edit/delete profiles with custom prompts)
- `config.json` for LLM endpoint, model, hotkey
- Settings panel in UI
- Default built-in profiles: Verbatim, Grammar Fix, Full Rewrite, Bullet Points

### Phase 5 — Polish and Edge Cases
**Why last:** Only polish what you know users actually see.

Deliverables:
- Error handling (no mic, CUDA not available, LLM timeout, injection failure)
- System tray icon + minimize behavior
- Startup with Windows (optional, user-controlled)
- Clipboard restore edge cases (non-text clipboard content warning)

---

## State Machine

The app has exactly five states. All components coordinate around this state:

```
IDLE
 │ hotkey press / record button click
 ▼
RECORDING
 │ hotkey release / button release
 ▼
TRANSCRIBING   (faster-whisper running in thread)
 │ transcription complete
 ▼
PROCESSING     (LLM API call in flight)
 │ LLM response received
 ▼
INJECTING      (clipboard swap + paste + restore)
 │ done
 ▼
IDLE
```

Any error at any stage → IDLE (with error badge in overlay). No intermediate states. No concurrent processing of a second recording while one is in-flight — the record button/hotkey is disabled during TRANSCRIBING, PROCESSING, and INJECTING states.

---

## Confirmed Library Choices

| Purpose | Library | Notes |
|---------|---------|-------|
| GUI overlay | PySide6 | LGPL, official Qt, handles frameless/topmost cleanly |
| Audio capture | sounddevice | PortAudio-backed, numpy-native callbacks |
| Transcription | faster-whisper | CTranslate2 backend, CUDA float16 |
| LLM client | openai (AsyncOpenAI) | Supports any OpenAI-compatible base_url |
| Win32 API | pywin32 (win32gui, win32clipboard) | GetForegroundWindow, clipboard ops |
| Global hotkey | pynput | GlobalHotKeys, no admin required for key listen |
| Text injection | pynput + pywin32 | pynput for Ctrl+V SendInput, pywin32 for HWND/clipboard |
| Config storage | stdlib json + os.path | No ORM needed; files in %APPDATA% |

---

## Known Risks and Open Questions

**Risk 1: HWND focus loss before injection**
If another window steals focus between recording-stop and injection (e.g. a notification popup), injection goes to the wrong window. Mitigation: the app re-focuses the snapshotted HWND via `SetForegroundWindow` immediately before paste. If that call fails (UIPI, minimized window), show an error — don't silently inject elsewhere.

**Risk 2: Clipboard-only terminals**
Older Windows Terminal versions (pre-1.17) and non-QuickEdit cmd.exe may not accept Ctrl+V. Mitigation: for Phase 2, test this explicitly. If Ctrl+V fails, fall back to `WM_PASTE` message sent directly to the terminal's edit control HWND. Document the limitation.

**Risk 3: Admin rights for hotkey hooks**
pynput does not require admin for key listening on Windows 11 in most cases. However, if the user runs an elevated (admin) application as the focused window, UIPI blocks input injection from a non-elevated process. Mitigation: document; optionally offer a "run as admin" mode.

**Risk 4: faster-whisper CUDA availability**
If CUDA is not available (driver not installed, wrong CUDA version), faster-whisper falls back to CPU — which is ~10x slower. Phase 1 should detect this at startup and warn the user, rather than silently running slow.

**Open Question: VAD (Voice Activity Detection)**
faster-whisper supports `vad_filter=True` with Silero VAD. This strips silence from the ends of recordings automatically. Enable this from day one — it reduces transcription latency and prevents Whisper from hallucinating text over silence. No additional library needed; it's bundled.
