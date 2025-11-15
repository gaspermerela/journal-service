# Architecture

High-level design decisions and trade-offs.

## How It Works

### Upload Flow

```
1. User authenticates (JWT)
2. Client POSTs MP3/M4A file
3. Validate file type + size
4. Generate UUID + timestamp filename
5. Save audio file to disk
6. Calculate audio duration (pydub)
7. Create database record (with duration_seconds)
   - If DB fails: delete audio file
8. Start background transcription (Whisper)
9. Return entry metadata + transcription_id
```

**Cleanup mechanism:** If database write fails, saved file is deleted automatically. No orphaned files.

## Key Decisions

### 1. Local Disk Storage (Not S3)

**Why:** MVP simplicity, zero cloud costs, single-server is enough \
**Trade-off:** No multi-server support, manual backups

File structure:
```
/data/audio/
  2025-01-31/
    {uuid}_{timestamp}.mp3
```

### 2. Async Architecture
**Why:** I/O-bound operations (file uploads, database, Whisper transcription)

### 3. Docker + rsync Deployment

**Why:** Simple enough for single-server MVP, no registry needed \
**Trade-off:** Manual process vs CI/CD automation

```bash
# Local machine
./docker/deploy.sh v1.0.0  # Build + upload

# Server
./run.sh v1.0.0            # Load + run
```

### 4. Alembic Migrations

**Why:** Version-controlled schema evolution, easy rollbacks

### 5. JWT Authentication

**Why:** User data isolation, stateless auth \
**Implementation:** Access and refresh tokens

## Current Limitations

- No rate limiting
- No file deletion API
- No file retrieval (only metadata)
- Single server only

## Tech Stack

- **FastAPI:** Async + auto OpenAPI docs
- **PostgreSQL**
- **SQLAlchemy:** Async ORM
- **Whisper:** Local speech-to-text
- **Ollama (llama3.2:3b):** LLM for text cleanup
- **pydub:** Audio duration calculation
- **JWT:** Token-based auth
- **Docker:** Consistent deployment
- **Pytest:** Testing

## Testing

Tests organized by type in subdirectories:

- **`tests/unit/`** - Business logic (no DB/external deps)
- **`tests/integration/`** - API routes + test database
- **`tests/e2e/`** - Full workflows with real services

Run subsets: `pytest tests/unit` (fast), `pytest tests/integration`, `pytest tests/e2e`