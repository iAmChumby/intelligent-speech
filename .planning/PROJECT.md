# Intelligent Speech

## What This Is

A Windows system-wide speech-to-text application with a persistent floating overlay. You select a processing profile, record your voice, and the app transcribes it locally, sends it through an LLM with the profile's custom instructions, then injects the polished result into whatever text field is currently focused. Built for power users who dictate to AI assistants and general text fields alike.

## Core Value

Turn raw speech into clean, intent-faithful text without manual editing — every dictated message is ready to send the moment you release the record button.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Persistent floating overlay that stays visible across all Windows apps (always-on-top, draggable)
- [ ] Profile system: user-defined profiles each with a name and custom LLM system prompt
- [ ] Push-to-talk or click-to-record UI — select profile, then record
- [ ] Local transcription via faster-whisper + CUDA (local-first, no per-call cost)
- [ ] Configurable LLM backend: base URL + optional API key (OpenAI-compatible, works with Ollama, LM Studio, Claude, OpenAI, etc.)
- [ ] Automatic text injection into the currently focused Windows text field after processing
- [ ] Built-in default profiles: Verbatim, Grammar Fix, Full Rewrite, Bullet Points
- [ ] Profile-level custom system prompt editor in settings

### Out of Scope

- macOS or mobile support — Windows-only for now
- Real-time streaming transcription — record-then-process is the UX
- Cloud-only transcription with no local option — local-first is a hard requirement
- Built-in LLM subscription — user provides their own API access or runs local

## Context

- **Hardware**: RTX 5070 Ti (16GB VRAM), Ryzen 7 7800X3D, 31GB RAM — ideal for faster-whisper large-v3, sub-second transcription for typical dictation lengths
- **Current tool**: Windows built-in Speech-to-Text — functional but raw transcript dumps with no grammar intelligence, choppy output, requires manual review before sending anywhere
- **Researched**: WhisperFlow (paid subscription, didn't investigate deeply), Handy (seemed primitive) — neither seemed to fit the vision
- **Primary use cases**: Dictating prompts to AI assistants (Claude Code, browser chat) AND general text dictation (docs, emails, notes)
- **Key pain point**: Raw transcripts waste tokens when sent to AI and require manual cleanup before sending — the app must produce send-ready output
- **Injection target**: Global — any focused text field in any Windows application

## Constraints

- **Platform**: Windows 11 only (initially)
- **Transcription**: Local-first via faster-whisper; remote fallback via configurable Whisper-compatible API endpoint
- **LLM**: Any OpenAI-compatible API (configurable base URL + optional API key) — no hard dependency on any provider
- **Cost model**: Zero mandatory per-call cost when using local models; user opts into API cost if they choose cloud
- **Research gate**: Must validate no existing tool satisfies requirements before committing to a full build

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Profile selected before recording | Intent is known at capture time — cleaner LLM prompts, more deterministic output | — Pending |
| Local-first transcription | RTX 5070 Ti makes faster-whisper sub-second; eliminates API cost and latency | — Pending |
| OpenAI-compatible LLM API | Works with every major provider and all local model servers without custom adapters | — Pending |
| Research before build | May find existing tool that satisfies 80%+ of requirements with less effort | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-16 after initialization*
