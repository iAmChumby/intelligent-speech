# Requirements — Intelligent Speech

**Version:** v1  
**Defined:** 2026-05-16  
**Status:** Active

---

## v1 Requirements

### CORE — Transcription Pipeline

- [ ] **CORE-01**: System captures microphone audio when recording is active (push-to-talk or hotkey-held)
- [ ] **CORE-02**: System transcribes captured audio locally using faster-whisper with CUDA acceleration (RTX GPU)
- [ ] **CORE-03**: System falls back to CPU transcription when CUDA is unavailable, with user-visible indication
- [ ] **CORE-04**: System automatically stops recording after a configurable silence period (VAD-based auto-stop via Silero VAD)
- [ ] **CORE-05**: System loads the Whisper model at startup in a background thread; recording is disabled until model is ready

### CORE — LLM Post-Processing

- [ ] **LLM-01**: System sends transcription + active profile's system prompt to a configurable LLM API endpoint
- [ ] **LLM-02**: LLM backend is configurable: base URL + optional API key (any OpenAI-compatible endpoint — Ollama, LM Studio, OpenAI, Claude, etc.)
- [ ] **LLM-03**: Profiles with LLM disabled skip the LLM call entirely; raw transcription is injected directly (zero LLM latency)
- [ ] **LLM-04**: System displays post-recording latency: transcription time and LLM time separately

### CORE — Text Injection

- [ ] **INJ-01**: System injects processed text into the Windows text field that was focused at the moment recording started
- [ ] **INJ-02**: Injection uses clipboard+paste (save clipboard → write text → SendInput Ctrl+V → restore clipboard) as the primary strategy
- [ ] **INJ-03**: System captures the target HWND at record-start, before the overlay takes focus
- [ ] **INJ-04**: User can cancel an in-progress or completed recording with Escape key; no text is injected on cancel
- [ ] **INJ-05**: System warns the user (non-blocking notification) when injection fails or the target field is inaccessible (e.g., elevated-privilege app)

### PROFILES — Built-in Defaults

- [ ] **PROF-01**: App ships with four built-in default profiles: Verbatim (LLM disabled), Grammar Fix, Full Rewrite, Bullet Points
- [ ] **PROF-02**: Built-in profiles are pre-loaded with appropriate system prompts and cannot be deleted (but can be duplicated)

### PROFILES — Custom Profiles

- [ ] **PROF-03**: User can create a new profile with a name and a custom LLM system prompt
- [ ] **PROF-04**: User can edit the name and system prompt of any custom profile
- [ ] **PROF-05**: User can delete any custom profile
- [ ] **PROF-06**: Each profile independently has LLM enabled or disabled (per-profile toggle)
- [ ] **PROF-07**: Profile definitions persist across app restarts (stored in %APPDATA%\IntelligentSpeech\)

### OVERLAY — Persistent Floating Toolbar

- [ ] **OVR-01**: App displays a persistent always-on-top floating toolbar visible across all Windows applications
- [ ] **OVR-02**: Toolbar is frameless, draggable, and remembers its screen position across restarts
- [ ] **OVR-03**: Toolbar displays the currently active profile name
- [ ] **OVR-04**: User can select a profile from the toolbar before recording (intent-first UX)
- [ ] **OVR-05**: Toolbar provides a clear visual state indicator: idle / recording / processing
- [ ] **OVR-06**: Toolbar does not steal focus from the active application when clicked for profile selection or record

### OVERLAY — Global Hotkey

- [ ] **HOT-01**: A global system-wide hotkey triggers start/stop recording regardless of which app is focused
- [ ] **HOT-02**: The global hotkey is configurable by the user

### SYSTEM — Tray & Lifecycle

- [ ] **SYS-01**: App runs as a system tray icon; main toolbar can be shown/hidden from tray
- [ ] **SYS-02**: App can be quit from the system tray right-click menu
- [ ] **SYS-03**: App launches on Windows startup (optional, user-configurable)

### SETTINGS — LLM & Model Config

- [ ] **SET-01**: Settings window allows configuring LLM base URL, API key, and model name
- [ ] **SET-02**: Settings window allows selecting the Whisper model size (tiny / base / small / medium / large-v3-turbo / large-v3)
- [ ] **SET-03**: Settings window allows configuring the silence timeout for VAD auto-stop

### DISTRIBUTION

- [ ] **DIST-01**: App is packaged as a standalone Windows executable (PyInstaller --onedir) with CUDA DLLs bundled
- [ ] **DIST-02**: On first launch, app downloads the selected Whisper model with a progress indicator
- [ ] **DIST-03**: App targets Windows 10/11 x64

---

## v2 Requirements (Deferred)

- Per-profile global hotkey assignment (Win+1 = Grammar Fix, Win+2 = Rewrite) — deferred to keep v1 hotkey simple
- Transcription history / searchable log — adds storage surface area; not core to the inject loop
- Custom vocabulary / user dictionary — faster-whisper handles most technical terms; can be handled via system prompt
- Profile import/export — useful for sharing but not blocking v1
- Remote Whisper-compatible transcription endpoint (as alternative to local) — local-first is v1
- macOS / Linux support — Windows-only until proven out
- Streaming / real-time transcription preview — significant complexity; record-then-process is v1 UX

---

## Out of Scope

- **Wake word / always-listening mode** — privacy concern; push-to-talk only
- **Speaker identification / diarization** — meeting tool feature, not dictation
- **Audio file batch transcription** — different product category
- **Built-in LLM subscription or API key bundling** — user provides their own
- **Real-time streaming transcription** — record-then-process is the stated UX
- **Mobile or browser extension** — Windows desktop only
- **Plugin/extension marketplace** — premature before core is solid
- **TTS (text-to-speech)** — different product direction

---

## Traceability

*Filled by roadmapper — maps each REQ-ID to a phase.*

| REQ-ID | Phase |
|--------|-------|
| *(populated by roadmap agent)* | |

---

*Last updated: 2026-05-16 after initial requirements definition*
