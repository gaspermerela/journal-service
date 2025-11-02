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

**Current - Phase 1 (Backend Backbone):**
- Upload `.mp3` audio files via REST API
- Store files with UUID-based naming and date organization
- PostgreSQL metadata storage
- Health monitoring and auto-generated API documentation

**Future Phases:**
- **Phase 2**: Audio transcription (Whisper)
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
# Upload audio file
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

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/upload` | POST | Upload audio file (multipart/form-data) |
| `/api/v1/entries/{id}` | GET | Retrieve entry metadata |
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