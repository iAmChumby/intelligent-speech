# Phase 1: CUDA & Transcription Spike - Context

**Gathered:** 2026-05-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Verify the CUDA dependency chain works on the target hardware (RTX 5070 Ti / Blackwell), load faster-whisper with GPU acceleration, and transcribe a pre-recorded test WAV — proving the transcription stack before any UI or audio capture investment.

Phase 1 is Python-only. The Electron + React frontend architecture applies from Phase 4 onward.

</domain>

<decisions>
## Implementation Decisions

### Architecture (cross-cutting — applies Phase 2+)

**IMPORTANT: The entire tech stack was established in this session. The prior planning artifacts (STACK.md, STATE.md) were AI-generated without user review. These decisions supersede all prior stack recommendations.**

- **D-01:** Frontend shell: **Electron** (handles always-on-top window, system tray, global hotkey)
- **D-02:** Frontend UI: **React** (rendered inside Electron BrowserWindow)
- **D-03:** Backend: **Python + FastAPI** running as a subprocess spawned by Electron main process
- **D-04:** IPC: **WebSocket over localhost** — React renderer talks to Python FastAPI; Electron main forwards hotkey events to Python via WebSocket
- **D-05:** Global hotkey: **Electron `globalShortcut`** module — NOT pynput (Electron handles hotkey → sends WebSocket message to Python → Python starts recording)
- **D-06:** Profile data: **Python backend owns it** — stored in `%APPDATA%\IntelligentSpeech\` as JSON or similar; Electron reads profiles from Python, not from Electron store
- **D-07:** Packaging: **PyInstaller --onedir** for the Python backend + **Electron Builder** for the full distributable. PyInstaller output included as `extraResources` inside the Electron app. Electron spawns the bundled `python.exe` subprocess at startup.

### Transcription Stack

- **D-08:** Library: **faster-whisper 1.2.1** — CTranslate2-backed, 4x faster than openai/whisper, native CUDA 12 support
- **D-09:** Default model: **large-v3-turbo** — 8x faster than large-v3 for English, ~1.5GB VRAM at int8_float16
- **D-10:** CUDA version lock: **CUDA 12 + cuDNN 9** (ctranslate2 >= 4.5 hard requirement). Install via: `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12==9.0.0`
- **D-11:** Blackwell (RTX 5070 Ti) compatibility: **MUST work on GPU — this is a hard gate**. If ctranslate2 does not support Blackwell compute capability, Phase 1 fails and the blocker must be resolved (newer ctranslate2 version, custom CUDA build, etc.) before proceeding. CPU-only fallback is NOT an acceptable Phase 1 outcome.

### Audio & VAD

- **D-12:** Audio capture: **sounddevice 0.5.5** — NumPy arrays directly, active maintenance, MIT license
- **D-13:** VAD: **silero-vad pip package** — PyPI package with torch dependency accepted. User explicitly chose this over ONNX/torch-free alternatives.

### Text Injection

- **D-14:** Strategy: **clipboard-swap + paste** — save clipboard → write text → SendInput Ctrl+V → restore clipboard (200ms delay before restore)
- **D-15:** Injection is handled by the **Python backend** using pynput for synthetic keypresses
- **D-16:** HWND captured at record-start moment (when Python receives the "start recording" WebSocket message from Electron hotkey handler) via `GetForegroundWindow()`. Not at inject time.

### LLM Client

- **D-17:** Library: **openai SDK 2.37.0** with `base_url` parameter — covers OpenAI, Ollama, LM Studio, and any OpenAI-compatible endpoint with zero code changes
- **D-18:** LLM calls run async on the Python FastAPI backend — never block the WebSocket event loop

### Python

- **D-19:** Python version: **3.11** — all libraries verified, CUDA extension ecosystem best-tested on 3.11

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Definition
- `.planning/ROADMAP.md` — Phase definitions, success criteria, and execution order
- `.planning/REQUIREMENTS.md` — 38 v1 requirements mapped across 9 phases (CORE, LLM, INJ, OVR, HOT, PROF, SET, SYS, DIST)
- `.planning/PROJECT.md` — Core value, active requirements, key decisions table, out-of-scope items

### Research Artifacts (informational — decisions in this CONTEXT.md supersede where they conflict)
- `.planning/research/STACK.md` — Library rationale and version details (note: GUI framework section is superseded by D-01 through D-07 above)
- `.planning/research/PITFALLS.md` — Critical, moderate, and minor risk catalog for all phases
- `.planning/research/ARCHITECTURE.md` — Architectural research (may conflict with Electron architecture — check against D-01 through D-07)

### Phase 1 Specific
- `.planning/research/PITFALLS.md §C1` — CUDA version trinity failure modes and prevention
- `.planning/research/PITFALLS.md §M5` — Cold start latency and model loading strategy
- `.planning/research/PITFALLS.md §G4` — Windows microphone privacy gate detection

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- No code exists yet — Phase 1 is the first implementation phase

### Established Patterns
- None yet — Phase 1 establishes the baseline project structure

### Integration Points
- Phase 1 Python code becomes the foundation of the Python FastAPI backend introduced in Phase 2
- `WhisperModel` singleton loaded at startup (never unloaded) carries forward to all subsequent phases
- CUDA device detection logic from Phase 1 is reused in Phase 9 first-run validation

</code_context>

<specifics>
## Specific Ideas

- User explicitly wants GPU transcription to work — if Blackwell is not supported by ctranslate2, find a fix before declaring Phase 1 complete
- Silero VAD with torch dependency: user accepted the ~1.5GB torch overhead. Do not look for lighter alternatives.
- Profile data in %APPDATA% owned by Python: Electron must ask Python for profile list, not maintain its own copy

</specifics>

<deferred>
## Deferred Ideas

- Visual styling / look-and-feel of the Electron overlay — Phase 4 concern
- React state management library (Redux, Zustand, Context API) — planner's call in Phase 4
- CSS/styling framework (Tailwind, CSS Modules) — planner's call in Phase 4
- JSON vs SQLite for profile storage format — planner's call in Phase 6
- pynput no longer needed for global hotkey (replaced by Electron globalShortcut) — remove from requirements.txt when writing Phase 5

</deferred>

---

*Phase: 1 — CUDA & Transcription Spike*
*Context gathered: 2026-05-16*
