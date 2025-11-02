# API Reference

Complete API documentation is available through the interactive Swagger UI at `/docs` when the service is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Quick Reference

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/upload` | POST | Upload MP3 audio file |
| `/api/v1/entries/{id}` | GET | Get entry metadata by UUID |
| `/health` | GET | Health check (includes DB status) |
| `/docs` | GET | Interactive API documentation (Swagger UI) |
| `/redoc` | GET | Alternative API documentation (ReDoc) |
| `/openapi.json` | GET | OpenAPI 3.0 specification |

## Quick Examples

**Upload audio file:**
```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@recording.mp3;type=audio/mpeg"
```

**Get entry metadata:**
```bash
curl "http://localhost:8000/api/v1/entries/{uuid}"
```

**Health check:**
```bash
curl "http://localhost:8000/health"
```