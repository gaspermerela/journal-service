# AI Journal Backend Service

[![License: Modified PolyForm NC](https://img.shields.io/badge/License-Modified%20PolyForm%20NC-blue.svg)](LICENSE.md)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-00a393.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://www.docker.com/)

## The Problem

Quality speech-to-text for smaller languages like Slovenian remains a challenge. Generic multilingual models often struggle with accuracy, while specialized solutions can be expensive or difficult to integrate. For professional sensitive recordings (therapists, healthcare workers, lawyers) there's an additional barrier: GDPR compliance when using cloud-based services.

## How This Started

I wanted to record dream journals by voice. That simple problem led me down a rabbit hole: transcription, LLM-based text cleanup, quality testing across providers. Eventually I realized that others face the same problem.

This project is my attempt to build a GDPR friendly, possibly even self-hosted, transcription service that prioritizes quality for Slovenian (and eventually other underserved languages).

## What It Does

A self-hostable REST API that:

1. **Accepts audio uploads** (voice memos, session recordings, dictation)
2. **Transcribes** using pluggable providers:
   - **Groq** (cloud Whisper) - Fast, multilingual, 99+ languages
   - **AssemblyAI** (cloud) - Speaker diarization, utterance-level timestamps
   - **Slovenian ASR** (RunPod) - Native Slovenian with PROTOVERB model, speaker diarization
3. **Cleans up** transcriptions with LLM post-processing:
   - **Groq** - For general text cleanup (cloud API)
   - **GaMS** (RunPod) - Native Slovenian LLM for optimal Slovenian text quality
4. **Encrypts everything** at rest (GDPR-compliant envelope encryption)
5. **Syncs** to Notion or exports for use elsewhere

The architecture is provider-agnostic. Swap transcription backends without changing your workflow. Compare quality across providers on the same audio. Analysis (themes, emotions, etc.) is handled by wrapper applications.

## Current State

This works for personal use today. I'm actively testing transcription quality and building toward a solution that could serve broader needs.

**What's done:**
- Multi-provider transcription (Groq Whisper, AssemblyAI, Slovenian ASR)
- Speaker diarization via AssemblyAI and Slovenian ASR (pyannote, NeMo)
- Slovenian-specific ASR with PROTOVERB model (3 diarization variants)
- LLM cleanup with Groq or GaMS (native Slovenian LLM)
- GDPR-compliant envelope encryption (all data encrypted at rest)
- Audio preprocessing pipeline (16kHz mono WAV, noise reduction)
- JWT authentication, multi-user support
- Per-request provider selection (switch providers without config changes)
- Notion integration with auto-sync
- React Native mobile + web frontend (separate repo)

**What's in progress:**
- Quality benchmarking framework across providers
- Additional language-specific model integrations

**What's not ready:**
- Production hardening (see [Known Issues](docs/known-issues.md))
- Formal security audit
- Validation beyond personal use

## Quick Start

```bash
# Clone and start (PostgreSQL included)
git clone <repo-url>
cd journal-service
docker compose -f docker-compose.dev.yml up -d

# Verify
curl http://localhost:8000/health
open http://localhost:8000/docs
```

See [API Reference](docs/api-reference.md) for authentication and endpoint examples.

## Architecture

FastAPI + PostgreSQL + async SQLAlchemy with pluggable transcription and LLM providers.

Key design decisions:
- **Provider abstraction**: Add new transcription or LLM services without touching core logic
- **Background processing**: Long-running tasks don't block API responses
- **Encryption by default**: Audio files and transcriptions encrypted at rest
- **Multi-tenant ready**: User isolation built in from the start
- **Backbone design**: Handles transcription + cleanup; analysis delegated to wrapper apps

[Full architecture details](docs/architecture.md)

## Potential Use Cases

- **Personal journaling**: Voice-first daily journals, dream logs, quick notes
- **Therapy/Psychology**: Session transcription with speaker diarization
- **Healthcare**: Dictation with domain-specific accuracy requirements
- **Slovenian language**: Native ASR and LLM for optimal quality
- **Underserved languages**: Where generic ASR falls short

## Known Issues

This service works for personal use but needs hardening before production deployment. See [docs/known-issues.md](docs/known-issues.md) for details.

## Documentation

- [Architecture](docs/architecture.md) - Design decisions
- [API Reference](docs/api-reference.md) - Endpoint documentation
- [Known Issues](docs/known-issues.md) - Current limitations
- [Docker Deployment](DOCKER.md) - Production setup

## License

This project is source-available under a [Modified PolyForm Noncommercial License](LICENSE.md).

**Free for:**
- Personal use, hobby projects, research
- Educational institutions

**Commercial use requires a license.** This includes non-profits, government, and any commercial entity. Contact me for licensing options.

📧 **Commercial inquiries:** [your-email@example.com](mailto:your-email@example.com)
