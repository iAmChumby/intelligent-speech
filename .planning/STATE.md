# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-16)

**Core value:** Turn raw speech into clean, intent-faithful text without manual editing — every dictated message is ready to send the moment you release the record button
**Current focus:** Phase 1 — CUDA & Transcription Spike

## Current Position

Phase: 1 of 9 (CUDA & Transcription Spike)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-05-16 — Roadmap created, 38 requirements mapped across 9 phases

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: none yet
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Init: PySide6 over PyQt6 (LGPL, distributable, official Qt binding)
- Init: faster-whisper large-v3-turbo as default model (~1.5GB VRAM, <2% WER delta vs large-v3)
- Init: Clipboard-swap+Ctrl+V as sole injection strategy (works in Electron, Win32, browsers, terminals)
- Init: HWND captured at record-start (hotkey fire), not at inject-time — prevents focus race condition
- Init: Sequential state machine: IDLE→RECORDING→TRANSCRIBING→PROCESSING→INJECTING→IDLE
- Init: WhisperModel loaded once at startup in background thread; never unloaded between recordings

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 1 critical: CUDA trinity version lock — ctranslate2 >= 4.5 requires CUDA 12.3+ AND cuDNN 9; must pip install nvidia-cublas-cu12 and nvidia-cudnn-cu12==9.0.0 explicitly
- Phase 1 critical: CUDA DLL hell for PyInstaller — static analysis misses dynamically-loaded CUDA DLLs; must add all CUDA DLLs to spec binaries list; test on clean VM (display driver only) before every release

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| v2 | Per-profile hotkey assignment | Deferred | Init |
| v2 | Transcription history / searchable log | Deferred | Init |
| v2 | Custom vocabulary / user dictionary | Deferred | Init |
| v2 | Profile import/export | Deferred | Init |
| v2 | Remote Whisper-compatible API endpoint | Deferred | Init |
| v2 | macOS / Linux support | Deferred | Init |
| v2 | Streaming / real-time transcription | Deferred | Init |

## Session Continuity

Last session: 2026-05-16
Stopped at: Roadmap written — ready to plan Phase 1
Resume file: None
