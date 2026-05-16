# Features Research — Intelligent Speech

**Researched:** 2026-05-16
**Mode:** Feasibility + Ecosystem (research-before-build gate)

---

## Existing Alternatives Audit

The table below evaluates each candidate against the six hard requirements:

| # | Requirement |
|---|-------------|
| R1 | Persistent floating overlay/toolbar (always visible, draggable) |
| R2 | Profile system — user-defined modes, each with a named custom LLM system prompt |
| R3 | Record → local transcription (faster-whisper/Whisper) → LLM post-process → inject into focused field |
| R4 | Configurable LLM backend (custom base URL + API key, any OpenAI-compatible provider) |
| R5 | Works globally across ALL Windows apps |
| R6 | Local-first, no mandatory subscription |

---

### SuperWhisper (Windows version — released Nov 2025)

| Criterion | Status | Notes |
|-----------|--------|-------|
| R1 Floating overlay | Partial | Compact recording widget exists; not a persistent toolbar |
| R2 Named profiles with custom system prompts | Partial | "Modes" system with custom prompts per mode — YES; but mode switching is hotkey-driven, not a persistent visual selector |
| R3 Local transcription + LLM + inject | YES | On-device Whisper/Parakeet models; cloud LLM post-processing; text injection into any Windows app |
| R4 Configurable LLM base URL | Partial | Supports OpenAI, Claude, Gemini, Groq, Ollama (added Dec 2025). Custom base URL for arbitrary OpenAI-compatible endpoints: documented for enterprise/self-hosted but not confirmed as a general user-facing field |
| R5 Global across all Windows apps | YES | System-wide dictation confirmed |
| R6 Local-first, no subscription | NO | Free tier is a 15-minute trial cap then hard-paywalled. Pro is $9.99/mo or ~$849 lifetime (2026 pricing). Local Whisper works offline but LLM post-processing requires cloud API calls or cloud account |

**Missing vs requirements:**
- No persistent always-on-screen toolbar; mode selection is not a first-class visual element
- Custom OpenAI-compatible base URL (Ollama, LM Studio) not confirmed as a general user setting
- Mandatory subscription to use beyond a 15-minute cap — violates local-first/no-subscription constraint
- Windows app is behind macOS in feature parity (launched Nov 2025, still catching up)

**Cost:** $9.99/mo or $849 lifetime  
**Verdict:** Closest commercial match but fails R4 (base URL), R6 (subscription), and R1 (no persistent toolbar). **Does not satisfy requirements.**

---

### TypeWhisper for Windows (Beta / GPLv3)

| Criterion | Status | Notes |
|-----------|--------|-------|
| R1 Floating overlay | Partial | "Dynamic Island" overlay appears during recording with waveform/status widgets. NOT a persistent always-on-screen toolbar between recordings |
| R2 Named profiles with custom system prompts | YES | Profiles + Workflows system. Workflows have templates for cleanup, translation, rewriting, extraction, custom prompts. Assign custom prompt per workflow. App/website-based auto-switching |
| R3 Local transcription + LLM + inject | YES | Local engines (SherpaOnnx, whisper.cpp, Granite Speech). LLM post-processing. System-wide text injection |
| R4 Configurable LLM base URL | YES | Supports Groq, OpenAI, Claude, Gemini, Cerebras, Cohere, Fireworks, OpenRouter, "OpenAI Compatible" (generic endpoint). Plugin system for adding custom LLM providers |
| R5 Global across all Windows apps | YES | System-wide dictation, hotkeys paste into any app |
| R6 Local-first, no subscription | YES | GPLv3 open source, no subscription, no account required, local-first by design. Commercial license from 5 EUR/mo for business use only |

**Missing vs requirements:**
- No persistent floating toolbar visible at all times between recordings. The overlay appears during recording only; there is no mode-selector widget that stays on screen
- Windows version is labeled "Beta" — not yet a stable 1.0 release. Feature parity with macOS is incomplete
- Local LLM provider uses LLamaSharp/GGUF, not faster-whisper (uses whisper.cpp instead). For this project's hardware (RTX 5070 Ti), faster-whisper with CUDA would be significantly faster, but whisper.cpp is functional
- Workflow/profile switching requires knowing hotkeys or digging into settings — no visual persistent UI for quick mode selection

**Cost:** Free (GPLv3). Commercial license 5 EUR/mo for business terms only.  
**Verdict:** Comes closest to satisfying all requirements — the LLM backend, profiles, and injection work. But the persistent always-on-screen toolbar (R1) is genuinely absent, and the Windows beta status introduces instability risk. **Does not fully satisfy requirements (missing R1).**

---

### SpeechPulse (Windows, one-time ~$20)

| Criterion | Status | Notes |
|-----------|--------|-------|
| R1 Floating overlay | Partial | Hotkey-mode-switching shows a transient overlay. No persistent always-on-screen toolbar |
| R2 Named profiles with custom system prompts | Partial | "AI Templates" with custom LLM instructions per template. "Speech Profiles" for voice settings. Not clear the two are unified into a single named "mode" concept |
| R3 Local transcription + LLM + inject | YES | Local Whisper/Parakeet models + LLM APIs. Types or pastes into any Windows app |
| R4 Configurable LLM base URL | YES | OpenAI-compatible API support; Ollama explicitly documented as a supported connection |
| R5 Global across all Windows apps | YES | System-wide; requires admin mode for admin-run apps |
| R6 Local-first, no subscription | YES | One-time ~$20 purchase; local transcription is the core model |

**Missing vs requirements:**
- No persistent always-on-screen toolbar
- AI Templates and Speech Profiles appear to be separate concepts, not a unified profile system where each profile = custom system prompt + name
- Real-time dictation focused (not record-then-process UX)
- UI is traditional Windows app window, not floating overlay paradigm

**Cost:** ~$20 one-time (30-day trial)  
**Verdict:** Solid local-first Windows STT with LLM, but missing the persistent floating toolbar and the unified profile-per-prompt concept. **Does not satisfy requirements (missing R1, R2 unification).**

---

### Handy (open source, cross-platform)

| Criterion | Status | Notes |
|-----------|--------|-------|
| R1 Floating overlay | Partial | Recording overlay exists during dictation; not persistent between recordings |
| R2 Named profiles with custom system prompts | NO | Post-processing is a single global toggle (`--toggle-post-process`), not a profile system with distinct named modes |
| R3 Local transcription + LLM + inject | YES | Local Whisper/Parakeet; LLM post-processing toggle; global paste injection |
| R4 Configurable LLM base URL | Unknown | LLM integration details not documented in reviewed sources |
| R5 Global across all Windows apps | YES | 21.8k GitHub stars; widely used across all platforms |
| R6 Local-first, no subscription | YES | Free, open source |

**Missing vs requirements:**
- No profile system — single global post-processing mode, no per-profile custom system prompts
- No persistent floating toolbar
- Windows version known to have Whisper crash issues on some configurations

**Cost:** Free (open source)  
**Verdict:** Good for basic local STT + single LLM polish pass, but the multi-profile system is absent. **Does not satisfy requirements (missing R1, R2).**

---

### Wispr Flow (formerly WhisperFlow, cross-platform)

| Criterion | Status | Notes |
|-----------|--------|-------|
| R1 Floating overlay | Partial | Compact recording button; not a persistent profile-selector toolbar |
| R2 Named profiles with custom system prompts | NO | Context-aware auto-formatting per app; no user-defined custom prompts |
| R3 Transcription + LLM + inject | YES | Cloud-based; sends to OpenAI/Meta servers |
| R4 Configurable LLM base URL | NO | Cloud-only; no custom backend |
| R5 Global across Windows apps | YES | Works system-wide on Windows |
| R6 Local-first, no subscription | NO | $15/mo subscription; cloud-mandatory (audio leaves device) |

**Cost:** $15/mo (2,000 words/week free tier)  
**Verdict:** Cloud-first subscription product. Fails R2, R4, R6 outright. **Does not satisfy requirements.**

---

### OpenWhispr (open source, cross-platform, v1.7.0 May 2026)

| Criterion | Status | Notes |
|-----------|--------|-------|
| R1 Floating overlay | Unknown | Not documented in reviewed sources |
| R2 Named profiles with custom system prompts | Unknown | "AI agent support" mentioned but profile-per-prompt system not documented |
| R3 Transcription + LLM + inject | YES | Local Whisper/Parakeet + cloud LLM agents; global hotkey paste |
| R4 Configurable LLM base URL | Partial | Supports local models and multiple cloud providers; custom base URL not confirmed |
| R5 Global across Windows apps | YES | Cross-platform, global hotkey injection |
| R6 Local-first, no subscription | YES | Free forever for local models; $8/mo Pro optional |

**Missing vs requirements:**
- Profile system with per-mode custom system prompts not confirmed
- Meeting-transcription focused (diarization, calendar) — different use case than quick dictation
- 3.2k stars, actively maintained but smaller community than Handy

**Cost:** Free (local); $8/mo Pro  
**Verdict:** Promising but the profile-per-prompt requirement is unconfirmed. Primarily positioned as a meeting tool. **Insufficient evidence to satisfy requirements — needs hands-on evaluation.**

---

### Murmure (open source, cross-platform, v1.8.1 Apr 2026)

| Criterion | Status | Notes |
|-----------|--------|-------|
| R1 Floating overlay | Roadmap | Streaming preview overlay is on the 1.9.0 roadmap — not yet shipped |
| R2 Named profiles with custom system prompts | NO | Ollama LLM integration exists but no named profile/mode system documented |
| R3 Transcription + LLM + inject | Partial | Local Parakeet transcription. LLM post-processing via Ollama. Text injection unclear |
| R4 Configurable LLM base URL | YES | Ollama explicitly supported (OpenAI-compatible endpoint) |
| R5 Global across Windows apps | Unknown | Windows 10+ supported; injection mechanism not confirmed |
| R6 Local-first, no subscription | YES | Free, open source (AGPL v3) |

**Cost:** Free  
**Verdict:** Early-stage, missing most UI requirements. **Does not satisfy requirements.**

---

### Talon Voice (Windows, free/paid)

| Criterion | Status | Notes |
|-----------|--------|-------|
| R1 Floating overlay | NO | No GUI toolbar; command-line and scripting paradigm |
| R2 Named profiles with custom system prompts | Partial | Highly scriptable via Python talon files; LLM integration via community plugins (talon-ai-tools) |
| R3 Transcription + LLM + inject | YES | Voice command → action; community LLM tools exist |
| R4 Configurable LLM base URL | Partial | Via Python scripting; not a user-facing settings field |
| R5 Global across Windows apps | YES | Deep system integration |
| R6 Local-first, no subscription | Partial | Free for individuals; power users version $15/mo |

**Cost:** Free (basic); $15/mo (power)  
**Verdict:** Designed for hands-free computing and voice commands, not dictation-with-LLM-cleanup. The profile system and floating toolbar would need to be built as scripts. Extreme power but high setup complexity. **Does not satisfy requirements out of the box.**

---

### Voice In (Chrome extension) / Dictation.io / Beey / Otter / Fireflies

All excluded from detailed review:
- **Voice In**: Chrome-only; no system-wide injection; no LLM post-processing profiles
- **Dictation.io**: Browser-based; no local transcription; no LLM post-processing
- **Beey / Otter / Fireflies**: Cloud meeting transcription tools — wrong category entirely (batch/async, not real-time dictation)
- **SuperWhisper iOS**: iOS-only variant; irrelevant to Windows-first requirement

---

## Build-vs-Buy Recommendation

**Verdict: Build from scratch.**

No existing tool satisfies all six requirements simultaneously. The most capable candidates fall short in specific ways:

**The blocking gap across all tools is R1 (persistent floating toolbar).** Every app surveyed treats the recording indicator as a transient element that appears during capture only. None ships a persistent always-on-screen widget that displays the current profile and provides a click-to-switch mode selector. This is the user's stated primary UX — selecting intent before recording — and it is simply not present in any reviewed tool.

**The second blocking gap is the unified profile model (R2).** TypeWhisper comes closest with its Workflows system, but it is workflow-trigger-based (fires when you're in a specific app or use a specific hotkey) rather than a deliberate "I am about to dictate in Grammar Fix mode" selection. SpeechPulse separates AI Templates from Speech Profiles. No tool treats a profile as (name + system prompt) as a first-class selectable entity.

**SuperWhisper** is the only tool that matches the overall UX vision but fails on subscription cost (R6) and has uncertain custom-base-URL support (R4). At $9.99/mo it introduces ongoing cost for a local-hardware use case that should be near-zero marginal cost.

**TypeWhisper (Windows Beta)** is the closest open-source alternative — it has LLM workflows, custom prompts, local transcription, and global injection — but is in beta, uses whisper.cpp (not faster-whisper), and lacks the persistent toolbar. If the persistent toolbar requirement were dropped, TypeWhisper would be worth a serious trial before building. Given that the toolbar is central to the stated UX, build is still warranted.

**The custom hardware context is also a factor.** An RTX 5070 Ti with 16GB VRAM running faster-whisper large-v3 is a competitive advantage that no off-the-shelf tool is optimized for. Most tools target CPU users or use cloud transcription; this project can deliver sub-second local transcription that no existing tool exposes as a first-class capability.

---

## Feature Categories (if building)

### Table Stakes

Features users expect from any STT dictation app. Absence makes the product feel broken.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Global hotkey to start/stop recording | Universal pattern; keyboard muscle memory | Low | Win32 `RegisterHotKey` or `keyboard` library |
| Text injection into focused field | Core value delivery; without this, just a clipboard tool | Medium | `pywinauto` / `pyautogui` / `win32api` SendInput; clipboard fallback for inaccessible fields |
| Visual recording indicator (active state feedback) | Users need to know when the mic is live | Low | Overlay color change / pulsing animation |
| Cancel recording without injecting | Accident recovery | Low | Escape key or dedicated cancel hotkey |
| Silence timeout / VAD | Prevents open-ended recordings | Low | faster-whisper has VAD built-in via `silero_vad` |
| Settings persistence | Profile definitions must survive app restart | Low | JSON config file in `%APPDATA%` |
| System tray icon + exit | Windows app convention | Low | `pystray` |
| CUDA acceleration toggle | Required for RTX hardware; graceful CPU fallback | Medium | faster-whisper `device="cuda"` vs `"cpu"` |
| Model selection (tiny/base/small/medium/large) | Different accuracy/speed tradeoffs per user | Low | Dropdown in settings; large-v3 as default |

---

### Differentiators

Features that distinguish this tool from everything reviewed above.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Persistent floating toolbar with active profile display | No existing tool has this; central to stated UX | Medium | WPF/Qt always-on-top window, draggable, remembers position |
| Per-profile custom LLM system prompt (create/edit/delete) | Every other tool has fixed templates; this gives full user control | Low-Medium | Profile model: `{name, system_prompt, hotkey}` stored as JSON |
| OpenAI-compatible base URL + API key per config | Works with Ollama, LM Studio, OpenAI, Claude, Groq — any endpoint | Low | Single `base_url` + `api_key` field; OpenAI Python client handles the rest |
| Select profile BEFORE recording (intent-first UX) | Existing tools select profile during or after; this matches how humans think | Low | Click profile in toolbar before pressing record button |
| Verbatim mode as a built-in first-class profile | Raw transcript with no LLM call — fastest possible path, useful for technical dictation | Low | Profile with no LLM step; just transcribe and inject |
| LLM call is optional and skippable per profile | Verbatim profile has zero LLM latency; other profiles opt in | Low | Profile flag: `llm_enabled: bool` |
| Processing latency display | Show "transcribed in 0.4s, LLM in 0.8s" — power user transparency | Low | Append to tray tooltip or small status widget |

---

### Anti-features (explicitly exclude)

Features to deliberately not build, with rationale.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Real-time streaming transcription | Adds significant complexity (streaming VAD, partial display, rollback); core UX is push-to-talk then inject, not live | Record-then-process pipeline; VAD to auto-stop on silence is sufficient |
| Cloud transcription backend (mandatory) | Violates local-first constraint; adds latency and cost | Support configurable remote Whisper-compatible endpoint as optional override only |
| Built-in LLM subscription or API key bundling | Forces ongoing cost; removes user control | User provides their own base URL + key; app never touches billing |
| Speaker identification / diarization | Meeting tool feature; not relevant to single-user dictation | Out of scope entirely |
| Audio file batch transcription | Different product (meeting notes tool); distracts from core UX | Out of scope |
| Mobile or macOS support | Platform complexity before Windows is solid | Windows-only until proven out |
| Wake word / always-listening mode | Privacy concern; increases background resource use | Push-to-talk only |
| GUI settings wizard / onboarding flow | Adds build time; target is power users who read docs | Plain settings window with clearly labeled fields |
| Custom vocabulary / user dictionary | Useful but complex; faster-whisper handles most technical terms adequately | Defer to v2 or handle via system prompt ("output as code identifiers") |
| Plugin/extension marketplace | Premature scaling; adds architecture overhead before core is solid | Hard-code the pipeline; expose JSON config for customization |
| Transcription history / search | Adds storage and UI surface area | Consider as a v2 feature; not core to the dictation-and-inject loop |
| TTS / text-to-speech | Different product direction | Out of scope |

---

## Complexity Notes

Implementation complexity per feature, calibrated for a Python-based desktop app on Windows 11.

| Feature | Complexity | Key Technical Challenge |
|---------|------------|------------------------|
| Persistent floating overlay (WPF/Tkinter/Qt always-on-top) | Medium | Win32 `WS_EX_TOPMOST` flag; dragging; position persistence; DPI awareness |
| Audio capture (push-to-talk) | Low | `sounddevice` or `pyaudio`; buffer to WAV in memory |
| faster-whisper local transcription (CUDA) | Low | Library is well-documented; `WhisperModel(device="cuda")`; first-load model caching |
| OpenAI-compatible LLM call | Low | `openai` Python client with configurable `base_url` and `api_key` |
| Text injection into focused Windows field | Medium-High | `SendInput` / `pywinauto` / clipboard fallback cascade; UAC-elevated apps require app elevation match; some fields block synthetic input |
| Profile CRUD (create/edit/delete/switch) | Low | In-memory dict + JSON file; no database needed |
| Global hotkey registration | Low | `keyboard` library or `RegisterHotKey` via ctypes |
| CUDA availability detection + fallback | Low | `torch.cuda.is_available()` or faster-whisper's own device detection |
| System tray icon | Low | `pystray` + `Pillow` for icon |
| Settings persistence | Low | `json` or `pydantic` model serialized to `%APPDATA%\IntelligentSpeech\config.json` |
| VAD-based auto-stop | Low | faster-whisper ships with Silero VAD integration; `vad_filter=True` |
| First-run model download UX | Medium | Progress display for large-v3 download (~3GB); integrity check; path management |

**Highest-risk feature:** Text injection. The Windows accessibility/input API landscape is fragmented — some applications accept `SendInput`, others only respond to clipboard paste, and UAC-elevated apps (e.g., Task Manager) block injection from non-elevated processes entirely. A robust cascade (SendInput → clipboard paste → clipboard-only warning) is needed.

**Second highest-risk:** Persistent overlay window. Keeping a window always-on-top without stealing focus from the active application requires careful Win32 flag management. `SetWindowPos(HWND_TOPMOST)` combined with `WS_EX_NOACTIVATE` is the standard pattern but has edge cases with fullscreen applications and some game overlays.

---

## Sources

- TypeWhisper Windows GitHub README: https://github.com/TypeWhisper/typewhisper-win
- TypeWhisper Windows Beta Docs: https://www.typewhisper.com/en/docs/windows/
- SuperWhisper Windows Changelog: https://superwhisper.com/changelog?platform=windows
- SuperWhisper Pricing (2026): https://www.getvoibe.com/resources/superwhisper-pricing/
- SpeechPulse Help: https://speechpulse.com/help/
- SpeechPulse LLM Blog: https://speechpulse.com/blog/how-to-enhance-your-dictation-in-real-time-using-large-language-models-on-windows-and-macos/
- Handy GitHub: https://github.com/cjpais/handy
- Handy HN Discussion: https://news.ycombinator.com/item?id=46628397
- Murmure GitHub: https://github.com/Kieirra/murmure
- OpenWhispr GitHub: https://github.com/OpenWhispr/openwhispr
- Wispr Flow Pricing: https://wisprflow.ai/pricing
- Wispr Flow vs SuperWhisper Comparison: https://www.getvoibe.com/resources/wispr-flow-vs-superwhisper/
- SuperWhisper Review 2026: https://spokenly.app/blog/superwhisper-review
