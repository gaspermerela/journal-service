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

**Future Phases:**
- **Phase 3**: LLM-based text cleanup and analysis
- **Phase 4**: Notion synchronization
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

**Test the API:**
```bash
# Upload and transcribe in one request
curl -X POST "http://localhost:8000/api/v1/upload-and-transcribe" \
  -F "file=@recording.mp3;type=audio/mpeg" \
  -F "entry_type=dream" \
  -F "language=en"

# Or upload only (requires separate transcription request)
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@recording.mp3;type=audio/mpeg"
```

**Stop services:**
```bash
# Stop (keeps data)
docker compose -f docker-compose.dev.yml down

# Reset everything (deletes data)
docker compose -f docker-compose.dev.yml down -v
```

**Production deployment (PostgreSQL on host):**

For production deployment with PostgreSQL running on the host via systemctl, see [DOCKER.md](DOCKER.md).


## API Endpoints

### Voice Entry Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/upload` | POST | Upload audio file (MP3 or M4A) |
| `/api/v1/entries/{id}` | GET | Retrieve entry metadata with primary transcription |

### Transcription
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/entries/{id}/transcribe` | POST | Trigger background transcription |
| `/api/v1/transcriptions/{id}` | GET | Get transcription status and result |
| `/api/v1/entries/{id}/transcriptions` | GET | List all transcriptions for an entry |
| `/api/v1/transcriptions/{id}/set-primary` | PUT | Set transcription as primary |

### System
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with database status |
| `/docs` | GET | Interactive API documentation (Swagger) |
| `/redoc` | GET | Alternative API documentation |

See [API Reference](docs/api-reference.md) for detailed request/response schemas.

## Architecture

FastAPI + PostgreSQL + async SQLAlchemy | [Full details](docs/architecture.md)

## Development

**Run tests:**
```bash
pytest -v                                    # All tests
pytest --cov=app --cov-report=term-missing  # With coverage
```

## Documentation

- [Architecture](docs/architecture.md) - Design decisions and trade-offs
- [API Reference](docs/api-reference.md) - Endpoints (or use `/docs` for interactive)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.