# Phase 1: Discussion Log

**Session:** 2026-05-16
**Outcome:** Full tech stack established (not Phase 1-only — cross-cutting)

---

## Summary

User revealed that the entire prior stack (PyQt6/PySide6, pure Python GUI) was AI-generated during project initialization without user review or confirmation. This session replaced the assumed stack with user-confirmed decisions.

---

## Discussion Sequence

### Area: Phase routing
**Question:** Phase 0 (requested) doesn't exist — what do you want to do?
**Answer:** Discuss Phase 1 instead

### Area: GUI Framework
**Question:** PyQt6 vs PySide6 (discrepancy between STACK.md and STATE.md)?
**Answer:** "I never confirmed a single part of the stack. The AI just chose for me and never mentioned shit."
**Follow-up:** Web UI (HTML/CSS/JS)
**Decision:** NOT PyQt6 or PySide6 — web-based UI

### Area: Web UI Shell
**Question:** Electron vs Tauri vs pywebview?
**Answer:** Electron

### Area: Frontend Framework
**Question:** React vs Svelte vs Vanilla vs Vue?
**Answer:** React

### Area: IPC Pattern
**Question:** Python HTTP/WebSocket server vs stdin/stdout?
**Answer:** Python HTTP/WebSocket server (recommended)

### Area: Python Backend Framework
**Question:** FastAPI vs Flask vs aiohttp?
**Answer:** FastAPI (recommended)

### Area: Blackwell GPU Compatibility
**Question:** CPU fallback acceptable vs must fix GPU?
**Answer:** Block on GPU — must fix (hard gate)

### Area: VAD Library
**Question:** silero-vad pip vs ONNX (no torch) vs skip for Phase 1?
**Answer:** silero-vad pip package (torch dependency accepted)

### Area: Global Hotkey
**Question:** Electron globalShortcut vs Python pynput?
**Answer:** Electron globalShortcut

### Area: Packaging
**Question:** PyInstaller inside Electron Builder vs other?
**Answer:** PyInstaller inside Electron Builder (recommended)

### Area: Profile Data Ownership
**Question:** Python backend vs Electron store?
**Answer:** Python backend owns it (%APPDATA%)

---

## Items Where Claude Had Discretion
- compute_type for Phase 1 spike (float16 vs int8_float16) — not discussed, planner decides
- JSON vs SQLite for profile storage — deferred to Phase 6 planner
- React state management library — deferred to Phase 4 planner
- CSS/styling framework — deferred to Phase 4 planner

---

## Prior Stack Items Superseded
| Component | Prior (AI-generated) | New (user-confirmed) |
|-----------|---------------------|---------------------|
| GUI framework | PyQt6 / PySide6 | Electron + React |
| System tray | Qt QSystemTrayIcon | Electron Tray API |
| Always-on-top window | Qt WindowStaysOnTopHint | Electron BrowserWindow flags |
| Global hotkey | pynput GlobalHotKeys | Electron globalShortcut |
| Packaging | PyInstaller alone | PyInstaller (Python) + Electron Builder (full app) |
| Backend server | N/A (monolith) | FastAPI (Python, localhost WebSocket) |
