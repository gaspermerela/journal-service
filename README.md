# AI Journal Backend Service

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-00a393.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://www.docker.com/)
[![Status: In Progress](https://img.shields.io/badge/status-in--progress-orange)]()

## Why This Project?

**Writing daily dream journals can be frustrating, especially in the middle of the night or right after waking up 🥱.**

This backend service solves that problem by offering a REST API for voice note uploads,
which can be used from iOS Shortcuts, a web app, or any other interface.
Once received, the audio is transcribed and cleaned up using ASR and LLM processing.
The final result can be automatically inserted into Notion or manually copied into any digital journal.

This approach could extend to general voice-based daily journaling.

  **Technical implementation:**
- **Modern async architecture** using FastAPI + SQLAlchemy async
- **Docker deployment pipeline** with Docker multi-platform builds and scripted automated deployment
- **Comprehensive testing** (unit, integration, end-to-end)
- **Database management** with Alembic migrations

## Features

**Current - Phase 1 (Backend Backbone):** ✅
- Upload `.mp3` and `.m4a` audio files via REST API
- Store files with UUID-based naming and date organization
- PostgreSQL metadata storage with entry_type support (dream, journal, meeting, note, etc.)
- Health monitoring and auto-generated API documentation

**Current - Phase 2 (Audio Transcription):** ✅
- Whisper-based audio transcription (configurable model via WHISPER_MODEL env var)
- Background transcription processing
- Multiple transcription support per entry
- Primary transcription selection
- Language detection and multi-language support

**Current - Phase 3 (Authentication & Security):** ✅
- JWT-based authentication with access and refresh tokens
- User registration and login

**Current - Phase 4 (LLM Text Cleanup):** ✅
- Ollama-based LLM text cleanup and analysis
- Background cleanup processing with status tracking
- Theme and emotion extraction from transcriptions
- Multiple cleanup attempts per transcription

**Current - Phase 5 (Notion Integration):** ✅
- Notion database validation & synchronization
- Encrypted API key storage
- Auto-sync after transcription cleanup (if enabled)

**Future Phases:**
- Frontend UI under consideration for future expansion

## Quick Start

**Local development/demo (PostgreSQL included):**

This is the easiest way to try the service - PostgreSQL is bundled in the same Docker Compose stack.

```bash
# Clone repository
git clone <repo-url>
cd journal-service

# Start Postgres and Journal backend services
docker compose -f docker-compose.dev.yml up -d

# Verify
curl http://localhost:8000/health
open http://localhost:8000/docs
```

**Using the API:**

The service requires authentication for all endpoints except `/health` and `/docs`.

```bash
# 1. Register and login via interactive docs
open http://localhost:8000/docs

# 2. Or use curl - see docs/api-reference.md for examples
```

See [API Reference](docs/api-reference.md) for complete authentication flow and endpoint examples.

**Stop services:**
```bash
# Stop (keeps data)
docker compose -f docker-compose.dev.yml down

# Reset everything (deletes data)
docker compose -f docker-compose.dev.yml down -v
```

**Production deployment (PostgreSQL on host):**

For production deployment with PostgreSQL running on the host via systemctl, see [DOCKER.md](DOCKER.md).

## API Documentation

- **Interactive Swagger UI:** http://localhost:8000/docs (try endpoints directly)
- **ReDoc:** http://localhost:8000/redoc (alternative format)
- **Detailed Reference:** [docs/api-reference.md](docs/api-reference.md) (curl examples, schemas)

## Architecture

FastAPI + PostgreSQL + async SQLAlchemy | [Full details](docs/architecture.md)

## Development

**Run tests:**
```bash
pytest -v                                    # All tests
pytest tests/unit                            # Unit tests only
pytest tests/integration                     # Integration tests (test DB)
pytest tests/e2e -m e2e_real                 # E2E tests (real services)
pytest --cov=app --cov-report=term-missing   # With coverage
```

## Known Issues & Future Improvements

**Note:** This service currently works well for personal use. The issues below should be fixed before production.

For detailed explanations and code examples, see **[docs/known-issues.md](docs/known-issues.md)**.

### 🔴 Critical

1. **No Automatic Retry for Failed Processing** ⚠️ - Temporary Ollama downtime causes permanent failures
2. **File Uploads Load Entire File Into Memory** - Redundant check loads full file into RAM (nginx already limits size)
3. **File Type Validation Relies on Client** - Can be bypassed by malicious users

### 🟡 High Priority (Before Scale)

4. **Missing Some Database Indexes** - Queries slow down with 10,000+ entries
5. **Missing Database Constraint for Primary Transcription** - No schema-level enforcement
6. **No Pagination on Transcription Lists** - Could return huge responses

### 🟢 Medium Priority

7. **No Graceful Shutdown** - Background tasks killed mid-processing
8. **Notion Sync Has Retry Infrastructure But No Execution** - Tracks retries but doesn't execute them

---

## Documentation

- [Architecture](docs/architecture.md) - Design decisions and trade-offs
- [API Reference](docs/api-reference.md) - Complete endpoint documentation with examples
- [Known Issues](docs/known-issues.md) - Detailed technical analysis of current limitations
- [Docker Deployment](DOCKER.md) - Production deployment guide

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.