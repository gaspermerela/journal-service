# Architecture

High-level design decisions and trade-offs.

## How It Works

### Upload Flow

```
1. Client POSTs MP3 file
2. Validate file type + size
3. Generate UUID + timestamp filename
4. Save mp3 file
5. Create database record (transaction)
   - If DB fails: delete mp3 file
7. Return entry metadata
```

No orphaned files if database write fails. File operations and DB writes stay in sync.

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
**Why:** Future phases need I/O-bound operations (Whisper API, LLM calls)

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

### 5. No Authentication (Yet)

**Current:** Open API, no auth required. If interest grows, auth will be added.

## Current Limitations

- No authentication
- No rate limiting
- No file retrieval (only metadata)
- No list/search entries endpoint
- No deletion
- Single server only

## Tech Stack

- **FastAPI:** Async + auto OpenAPI docs
- **PostgreSQL**
- **SQLAlchemy:** Async ORM
- **Docker:** Consistent deployment
- **Pytest:** Testing

## Testing

- **Unit tests:** Business logic (validators, storage, database)
- **Integration tests:** Full request cycle with test DB
- **E2E tests:** Real HTTP requests to running service