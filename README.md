# AI Journal Backend Service

[![License: PolyForm Noncommercial](https://img.shields.io/badge/License-PolyForm%20Noncommercial-blue.svg)](LICENSE.md)
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
2. **Transcribes** using pluggable providers (local Whisper, Groq, AssemblyAI, or language-specific models)
3. **Cleans up** transcriptions with LLM post-processing (fixes grammar, adds punctuation, structures text)
4. **Analyzes** content (extracts themes, emotions, ...)
5. **Encrypts everything** at rest (GDPR-compliant envelope encryption)
6. **Syncs** to Notion or exports for use elsewhere

The architecture is provider-agnostic. Swap transcription backends without changing your workflow. Compare quality across providers on the same audio.

## Current State

This works for personal use today. I'm actively testing transcription quality and building toward a solution that could serve broader needs.

**What's done:**
- Multi-provider transcription (Whisper, Groq, AssemblyAI)
- LLM cleanup with Ollama or Groq
- GDPR-compliant envelope encryption (all data encrypted at rest)
- JWT authentication, multi-user support
- Notion integration
- React Native mobile + web frontend (separate repo)

**What's in progress:**
- Speaker diarization (for conversations with multiple speakers)
- Slovenian-specific model integration (RSDO, fine-tuned Whisper)
- Quality benchmarking framework

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
- **Provider abstraction**: Add new transcription services without touching core logic
- **Background processing**: Long-running tasks don't block API responses
- **Encryption by default**: Audio, transcriptions, and analysis encrypted at rest
- **Multi-tenant ready**: User isolation built in from the start

[Full architecture details](docs/architecture.md)

## Potential Use Cases

- **Personal journaling**: Voice-first daily journals, dream logs, quick notes
- **Therapy/Psychology**: Session transcription with speaker separation (in progress)
- **Healthcare**: Dictation with domain-specific accuracy requirements
- **Underserved languages**: Where generic ASR falls short

## Known Issues

This service works for personal use but needs hardening before production deployment. See [docs/known-issues.md](docs/known-issues.md) for details.

## Documentation

- [Architecture](docs/architecture.md) - Design decisions
- [API Reference](docs/api-reference.md) - Endpoint documentation
- [Known Issues](docs/known-issues.md) - Current limitations
- [Docker Deployment](DOCKER.md) - Production setup

## License

This project is source-available under the [PolyForm Noncommercial License 1.0.0](LICENSE.md).

You may view, learn from, and use this software for personal, non-commercial purposes. For commercial licensing inquiries, please open an issue or contact the maintainer.
