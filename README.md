# AI Journal Backend Service

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-00a393.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://www.docker.com/)
[![Status: In Progress](https://img.shields.io/badge/status-in--progress-orange)]()

## Why This Project?

**Writing daily dream journals can be frustrating, especially right after waking up.**  
This backend service tries to solve that problem by letting you record voice notes,  
send them to a server via iOS Shortcuts or web app, and transform them into clean,  
fluent entries using ASR (transcription) and LLM (transcription cleanup) processing pipelines.  
The final result can be automatically inserted into your Notion database or manually copied into any digital journaling platform of your choice.

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
- Audio transcription (Whisper)
- LLM-based text cleanup and analysis
- Notion synchronization
- Frontend UI under consideration for future expansion

## Quick Start

**With Docker (recommended):**
```bash
# Clone and configure
git clone <repo-url>
cd journal-service
cp .env.example .env

# Start services
docker-compose up -d

# Verify
curl http://localhost:8000/health
```

**Local development:**
```bash
# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL database
docker run --name postgres \
  -e POSTGRES_USER=journal_user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=postgres \
  -p 5432:5432 -d postgres:17

docker exec -i postgres bash -c \
  "PGPASSWORD=password psql -U journal_user -d postgres -c 'CREATE SCHEMA IF NOT EXISTS journal;'"

# Configure and run
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

**Test it:**
```bash
# Upload audio file
  curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@recording.mp3;type=audio/mpeg"

# View API docs
open http://localhost:8000/docs
```

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

**Stack:**
- **Framework**: FastAPI with automatic OpenAPI docs
- **Database**: PostgreSQL with SQLAlchemy async ORM
- **Migrations**: Alembic
- **Testing**: pytest
- **Deployment**: Docker 
- **Server**: Uvicorn ASGI server

**Project Structure:**
```
journal-service/
├── app/                  # Application code
│   ├── routes/          # API endpoints
│   ├── services/        # Business logic
│   ├── models/          # Database models
│   └── schemas/         # Pydantic validation
├── tests/               # Comprehensive test suite
├── alembic/             # Database migrations
├── docker/              # Deployment scripts
└── docs/                # Technical documentation
```

See [Getting Started Guide](docs/getting-started.md) for detailed setup instructions.

## Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=term-missing

# End-to-end tests (requires running service)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pytest tests/test_e2e.py -v
```

See [Testing Guide](docs/testing.md) for comprehensive test documentation.

## Deployment

Simplified deployment pipeline for remote servers:

```bash
# Local: Build and upload image
export SERVER_IP=your.server.ip
./docker/deploy.sh v1.0.0

# Server: Deploy uploaded image
ssh user@server
cd /path/to/journal-service
./run.sh v1.0.0
```

See [Deployment Guide](docs/deployment.md) for detailed instructions.

## Documentation

- [Getting Started](docs/getting-started.md) - Detailed setup and configuration
- [API Reference](docs/api-reference.md) - Complete endpoint documentation
- [Testing Guide](docs/testing.md) - Running and writing tests
- [Deployment Guide](docs/deployment.md) - Production deployment pipeline
- [Database Schema](docs/database-schema.md) - Schema design and migrations
- [Architecture](docs/architecture.md) - Design decisions and structure

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.