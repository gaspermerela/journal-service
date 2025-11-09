# API Reference

Complete API documentation is available through the interactive Swagger UI at `/docs` when the service is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Quick Reference

### Voice Entry Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/upload-and-transcribe` | POST | **Recommended**: Upload audio and start transcription in one request |
| `/api/v1/upload` | POST | Upload audio file only (MP3 or M4A) |
| `/api/v1/entries/{id}` | GET | Get entry metadata with primary transcription |

### Transcription

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/entries/{id}/transcribe` | POST | Trigger background transcription for an entry |
| `/api/v1/transcriptions/{id}` | GET | Get transcription status and result |
| `/api/v1/entries/{id}/transcriptions` | GET | List all transcriptions for an entry |
| `/api/v1/transcriptions/{id}/set-primary` | PUT | Set a transcription as primary for display |

### System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (includes DB status) |
| `/docs` | GET | Interactive API documentation (Swagger UI) |
| `/redoc` | GET | Alternative API documentation (ReDoc) |
| `/openapi.json` | GET | OpenAPI 3.0 specification |

## Quick Examples

### Voice Entry Workflow

**Upload audio file:**
```bash
# Default entry_type (dream)
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@recording.mp3;type=audio/mpeg"

# Specify entry_type
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@recording.mp3;type=audio/mpeg" \
  -F "entry_type=journal"
```

The `entry_type` parameter is optional and defaults to "dream". Supported types: dream, journal, meeting, note, or any custom type.

**Get entry metadata:**
```bash
curl "http://localhost:8000/api/v1/entries/{entry_id}"
```

Returns entry metadata including primary transcription if available.

### Transcription Workflow

**1. Trigger transcription:**
```bash
curl -X POST "http://localhost:8000/api/v1/entries/{entry_id}/transcribe" \
  -H "Content-Type: application/json" \
  -d '{"language": "auto"}'
```

Returns `transcription_id` for status tracking. Transcription runs in background.

**2. Check transcription status:**
```bash
curl "http://localhost:8000/api/v1/transcriptions/{transcription_id}"
```

Status values: `pending`, `processing`, `completed`, `failed`

**3. List all transcriptions for an entry:**
```bash
curl "http://localhost:8000/api/v1/entries/{entry_id}/transcriptions"
```

**4. Set primary transcription (optional):**
```bash
curl -X PUT "http://localhost:8000/api/v1/transcriptions/{transcription_id}/set-primary"
```

### System

**Health check:**
```bash
curl "http://localhost:8000/health"
```