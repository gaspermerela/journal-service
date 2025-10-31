# AI Journal Backend Service Specification

## 🧠 Project Overview

This project is a backend service for a voice-based dream journaling application. 
Users record dreams as `.mp3` audio files (e.g., via iOS Shortcuts or mobile app) 
and submit them to the backend. The system stores the audio and related metadata. 
This is **Phase 1** of development.

## ✅ Features (Current Scope)

Implemented in this version:

- Accept `.mp3` file uploads via HTTP POST. Audio file represent voice recording in Slovenian or English language.
- Save uploaded audio files to disk with unique filenames
- Store metadata in a PostgreSQL database

## 💤 Deferred Features (Future Phases)

Not implemented now but the system should be structured to support:

- Transcribing audio to text with open-sourced model (e.g., via Whisper)
- LLM-based text cleanup to generate fluent dream entries
- Dream motif and entity extraction
- Syncing final text to Notion

In the distant future, the service may extend to support daily/weekly journaling
via multiple mp3 files representing journal entries throughout the day/week.

---

## ⚙️ Stack Requirements

**Selected Stack:**

- ✅ **Web Framework**: FastAPI (async, modern, auto-documentation, type hints)
- ✅ **Database**: PostgreSQL
- ✅ **ORM**: SQLAlchemy (with async support via asyncpg)
- ✅ **Migrations**: Alembic
- ✅ **Logging**: Python's `logging` module with structured text output
- ✅ **Environment Config**: `python-dotenv`
- ✅ **Validation**: Pydantic (built into FastAPI)
- ✅ **Testing**: pytest + httpx (for async tests)
- ✅ **Containerization**: Docker (Dockerfile + docker-compose)
- ✅ **WSGI Server**: Uvicorn (ASGI server for FastAPI)

---

## 🌐 API Endpoints

### `POST /api/v1/upload`
Upload an audio file for dream journaling.

**Request:**
- Content-Type: `multipart/form-data`
- Field name: `file`
- Accepted file types: `.mp3`
- Max file size: 100 MB (configurable via `.env`)

**Response (Success - 201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "dream_recording.mp3",
  "saved_filename": "550e8400-e29b-41d4-a716-446655440000_20250131T143022.mp3",
  "file_path": "/data/audio/2025-01-31/550e8400-e29b-41d4-a716-446655440000_20250131T143022.mp3",
  "uploaded_at": "2025-01-31T14:30:22.123456Z",
  "message": "File uploaded successfully"
}
```

**Response (Error - 4xx/5xx):**
```json
{
  "detail": "Error description",
  "error_code": "INVALID_FILE_TYPE"
}
```

**Status Codes:**
- `201`: File uploaded and saved successfully
- `400`: Invalid request (wrong file type, missing file, etc.)
- `413`: File too large
- `500`: Server error (storage failure, database error)

### `GET /api/v1/entries/{id}`
Retrieve metadata for a specific dream entry.

**Response (Success - 200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "dream_recording.mp3",
  "saved_filename": "550e8400-e29b-41d4-a716-446655440000_20250131T143022.mp3",
  "file_path": "/data/audio/2025-01-31/550e8400-e29b-41d4-a716-446655440000_20250131T143022.mp3",
  "uploaded_at": "2025-01-31T14:30:22.123456Z"
}
```

**Status Codes:**
- `200`: Entry found
- `404`: Entry not found

### `GET /health`
Health check endpoint for monitoring.

**Response (Success - 200 OK):**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-01-31T14:30:22.123456Z"
}
```

### `GET /docs`
Auto-generated API documentation (FastAPI Swagger UI).

### `GET /redoc`
Alternative API documentation (ReDoc).

---

## 📂 File Storage

**Storage Structure:**
- Base path: `/data/audio/` (configurable via `AUDIO_STORAGE_PATH` in `.env`)
- Subfolder structure: `/data/audio/YYYY-MM-DD/`
- Example full path: `/data/audio/2025-01-31/550e8400-e29b-41d4-a716-446655440000_20250131T143022.mp3`

**Filename Format:**
- Pattern: `{uuid}_{timestamp}.mp3`
- UUID: UUID4 format
- Timestamp: ISO 8601 compact format `YYYYMMDDTHHmmss`
- Example: `550e8400-e29b-41d4-a716-446655440000_20250131T143022.mp3`

**Behavior:**
- Directories created automatically if they don't exist
- Original filename preserved in database metadata
- File permissions set to 644 (readable by owner/group)
- Atomic write operations (write to temp, then move)

---

## 🗃️ Database

**Configuration:**
- Database name: `journal` (configurable via `.env`)
- All connection parameters configurable via `.env`:
  - Host, Port, Username, Password, Database name
- Connection pooling enabled (SQLAlchemy async engine)
- Migration management via Alembic

**Schema:**

**Table: `dream_entries`**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier (UUID4) |
| `original_filename` | VARCHAR(255) | NOT NULL | Original name of uploaded file |
| `saved_filename` | VARCHAR(255) | NOT NULL, UNIQUE | UUID-based filename on disk |
| `file_path` | TEXT | NOT NULL | Absolute path to saved file |
| `uploaded_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Upload timestamp (UTC) |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Record creation time |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last update time |

**Indexes:**
- Primary key on `id`
- Index on `uploaded_at` (for time-based queries)
- Unique index on `saved_filename`

**Future Schema Extensions:**
- `transcription` column (TEXT) for audio-to-text output
- `cleaned_text` column (TEXT) for LLM-processed content
- `language` column (VARCHAR) for detected language
- `motifs` column (JSONB) for extracted themes
- `synced_to_notion` column (BOOLEAN) for sync status
- `notion_page_id` column (VARCHAR) for Notion reference

---

## 🪵 Logging

**Configuration:**
- Log level configurable via `LOG_LEVEL` in `.env` (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Default level: INFO
- Output: stdout (suitable for Docker/container environments)
- Format: Structured text with timestamp, level, module, and message

**Log Format Example:**
```
2025-01-31 14:30:22.123 | INFO | app.routes.upload | File upload request received | ip=192.168.1.100 filename=dream_recording.mp3 size=5242880
2025-01-31 14:30:22.456 | INFO | app.services.storage | File saved successfully | saved_path=/data/audio/2025-01-31/550e8400...mp3
2025-01-31 14:30:22.789 | INFO | app.services.database | Database record created | entry_id=550e8400-e29b-41d4-a716-446655440000
```

**What Gets Logged:**
- **Request Level**: HTTP method, path, IP address, user agent, request ID
- **Upload Processing**: Original filename, file size, content type validation
- **File Operations**: Save location, success/failure, disk usage
- **Database Operations**: Query type, success/failure, execution time
- **Errors**: Full stack trace, context data, request ID for tracing
- **Performance**: Response times, slow queries (>1s)

**Sensitive Data Handling:**
- Never log file contents
- Never log full file paths in non-ERROR logs (use relative paths)
- Never log database credentials

---

## ⚙️ Server Configuration

**Application Settings:**
- **Host**: `0.0.0.0` (configurable via `HOST`)
- **Port**: `8000` (configurable via `PORT`)
- **Workers**: 1 (can be increased for production via `WORKERS`)
- **Reload**: Enabled in development, disabled in production
- **CORS**: Configurable origins via `CORS_ORIGINS` (comma-separated list)
  - Default: Allow all origins in development
  - Production: Specify allowed origins explicitly

**Request Limits:**
- Max file size: 100 MB (configurable via `MAX_FILE_SIZE_MB`)
- Request timeout: 60 seconds
- Max concurrent uploads: Limited by worker count

**Graceful Shutdown:**
- Handles SIGTERM and SIGINT signals
- Completes in-flight requests before shutdown
- Closes database connections cleanly

---

## 🔧 Environment Variables

All configuration via `.env` file. See `.env.example` for template.

**Required Variables:**
```bash
# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=journal
DATABASE_USER=journal_user
DATABASE_PASSWORD=secure_password

# Application Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Storage Configuration
AUDIO_STORAGE_PATH=/data/audio
MAX_FILE_SIZE_MB=100
```

**Optional Variables:**
```bash
# CORS Configuration (comma-separated)
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Worker Configuration
WORKERS=1

# Database Pool Configuration
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# Development/Debug
DEBUG=false
RELOAD=false
```

**Docker-Specific:**
```bash
# Used in docker-compose.yml
POSTGRES_USER=journal_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=journal
```

---

## 🚨 Error Handling & Rollback Strategy

**Transaction Management:**
- All database writes wrapped in transactions
- Automatic rollback on any failure
- File operations performed before database commits

**Error Scenarios:**

1. **Invalid File Type**
   - HTTP 400 response
   - No file saved, no database entry

2. **File Too Large**
   - HTTP 413 response
   - No file saved, no database entry

3. **Disk Write Failure**
   - HTTP 500 response
   - Attempted file deletion if partial write
   - No database entry created

4. **Database Connection Failure**
   - HTTP 500 response
   - File saved but orphaned (can be cleaned up later)
   - Logged with full context for manual recovery

5. **Database Write Failure**
   - HTTP 500 response
   - Transaction rollback
   - Saved file deleted to maintain consistency

**Retry Logic:**
- No automatic retries (client responsible)
- Idempotency: Same file can be uploaded multiple times
- Each upload creates new UUID/entry

**Monitoring Hooks:**
- All errors logged with request ID for tracing
- Database health checked on startup and in `/health` endpoint
- Disk space not monitored (rely on system-level monitoring)

---

## 🧪 Tests

**Test Structure:**
- Unit tests: Test individual components (storage, validation, etc.)
- Integration tests: Test full request/response cycle with test database
- Test database: Separate from main database, cleaned between tests
- Fixtures: Provide sample MP3 files for testing

**Test Coverage:**
- ✅ File upload with valid MP3 file
- ✅ File upload with invalid file type
- ✅ File upload exceeding size limit
- ✅ File storage logic (directory creation, naming)
- ✅ Database operations (create, retrieve)
- ✅ Health endpoint
- ✅ Error handling and rollback scenarios

**Running Tests:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_upload.py
```

---

## 📁 Project Structure

```
journal-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management (.env loading)
│   ├── database.py             # Database connection and session management
│   ├── models/
│   │   ├── __init__.py
│   │   └── dream_entry.py      # SQLAlchemy models
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── dream_entry.py      # Pydantic schemas for request/response
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── upload.py           # Upload endpoint
│   │   ├── entries.py          # Entry retrieval endpoints
│   │   └── health.py           # Health check endpoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── storage.py          # File storage logic
│   │   └── database.py         # Database operations
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── logging.py          # Request logging middleware
│   └── utils/
│       ├── __init__.py
│       ├── logger.py           # Logging configuration
│       └── validators.py       # File validation utilities
├── alembic/
│   ├── versions/               # Migration files
│   └── env.py                  # Alembic configuration
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_upload.py          # Upload endpoint tests
│   ├── test_storage.py         # Storage service tests
│   ├── test_database.py        # Database service tests
│   └── fixtures/
│       └── sample.mp3          # Test audio file
├── docs/
│   ├── overview.md
│   ├── endpoints.md
│   ├── database-schema.md
│   ├── logging.md
│   ├── future-features.md
│   └── changelog.md
├── data/
│   └── audio/                  # Audio file storage (created at runtime)
├── Dockerfile
├── docker-compose.yml
├── alembic.ini                 # Alembic configuration
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .env                       # Environment variables (gitignored)
├── .gitignore
├── .dockerignore
└── README.md                  # This file
```

**Key Design Principles:**
- **Separation of Concerns**: Routes, services, and models are separated
- **Async/Await**: All I/O operations are async
- **Dependency Injection**: FastAPI's DI system for database sessions
- **Type Hints**: Full type annotation for better IDE support
- **Error Handling**: Centralized exception handling
- **Configuration**: All config loaded from environment variables

---

## 🐳 Dockerization

**Dockerfile:**
- Multi-stage build for optimized image size
- Based on Python 3.11+ slim image
- Non-root user for security
- Health check included

**docker-compose.yml:**
- **App service**: FastAPI application
  - Exposed port: 8000
  - Volume: `/data/audio` for persistent storage
  - Depends on database service
  - Auto-restart on failure
- **PostgreSQL service**:
  - Version: 15+
  - Volume for database persistence
  - Health check for readiness
- **Network**: Internal bridge network for service communication

**Volumes:**
- `postgres_data`: Database persistence
- `audio_data`: Audio file storage persistence

**Docker Commands:**
```bash
# Build and start all services
docker-compose up --build

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

---

## 🚀 Quick Start

**Prerequisites:**
- Docker & Docker Compose installed
- OR Python 3.11+ and PostgreSQL 15+

**Option 1: Docker (Recommended)**
```bash
# 1. Clone the repository
git clone <repo-url>
cd journal-service

# 2. Copy and configure environment variables
cp .env.example .env
# Edit .env with your settings

# 3. Start services
docker-compose up --build

# 4. API available at http://localhost:8000
# 5. View docs at http://localhost:8000/docs
```

**Option 2: Local Development**
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up database
# Create PostgreSQL database: journal

# 3. Configure environment
cp .env.example .env
# Edit .env with your local settings

# 4. Run migrations
alembic upgrade head

# 5. Start application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. API available at http://localhost:8000
```

**Testing the API:**
```bash
# Upload a file
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/recording.mp3"

# Check health
curl "http://localhost:8000/health"

# Get entry by ID
curl "http://localhost:8000/api/v1/entries/{entry-id}"
```

---

## 📈 Future Extension Hooks

The code should be modular to allow:

- Adding a transcription module
- Adding LLM prompt-based cleanup
- Notion integration
- Metadata tagging system
- API key or auth layer

---

## 🔐 Security & Safety

- Only `.mp3` files allowed for now
- Limit max file size (e.g., 100 MB)
- Sanitize and validate all inputs

---

## 📌 Summary

This project is a robust, containerized backend for dream audio journaling. 
The current version handles file storage and metadata, while future phases 
will enable full AI processing and integration.

## 📜 Documentation

During AI based and manual development, we must maintain detailed documentation in the
`docs/` directory. It should be structured in multiple `.md` files, for example (but not necessarily like this):
- `overview.md` - High-level system architecture and design
- `endpoints.md` - Detailed API endpoint documentation
- `database-schema.md` - Database schema with relationships
- `logging.md` - Logging standards and examples
- `future-features.md` - Planned enhancements and roadmap
- `changelog.md` - Version history and changes

---

## 🛠️ Development Workflow

**Adding New Features:**
1. Create feature branch from main
2. Update documentation in `docs/` if needed
3. Implement feature with tests
4. Run tests: `pytest --cov=app`
5. Update `docs/changelog.md`
6. Create pull request

**Database Migrations:**
```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Review generated migration file
# Edit if needed

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

**Code Quality:**
- Type hints required for all functions
- Docstrings for complex functions
- Follow PEP 8 style guide
- Keep functions small and focused
- Separate business logic from routes

**Best Practices:**
- Always use async/await for I/O operations
- Handle exceptions at service layer
- Log all important operations
- Never commit `.env` file
- Test error scenarios, not just happy paths
- Keep database sessions short-lived

---

## 🔍 Troubleshooting

**Database Connection Issues:**
```bash
# Check database is running
docker-compose ps

# View database logs
docker-compose logs postgres

# Connect to database directly
docker-compose exec postgres psql -U journal_user -d journal
```

**File Storage Issues:**
```bash
# Check directory permissions
ls -la /data/audio

# Check disk space
df -h

# View app logs
docker-compose logs app
```

**Application Not Starting:**
```bash
# Check environment variables
cat .env

# Verify all required variables are set
# Check for syntax errors in .env

# View full error logs
docker-compose up
```

---

## 📄 License

This project is private and proprietary.

---

## 👤 Author

Developed for personal dream journaling and AI processing experimentation.
