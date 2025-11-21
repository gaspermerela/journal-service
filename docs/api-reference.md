# API Reference

Complete API documentation is available through the interactive Swagger UI at `/docs` when the service is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Authentication

All API endpoints (except `/health`, `/docs`, `/redoc`, and authentication endpoints) require authentication using JWT Bearer tokens.

### Authentication Flow

1. **Register** a new user account (`/api/v1/auth/register`)
2. **Login** to receive access and refresh tokens (`/api/v1/auth/login`)
3. **Include the access token** in the `Authorization` header for all protected endpoints
4. **Refresh** your access token when it expires using the refresh token (`/api/v1/auth/refresh`)

Access tokens expire after `ACCESS_TOKEN_EXPIRE_DAYS` days (7 by default). Refresh tokens expire after `REFRESH_TOKEN_EXPIRE_DAYS` days (30 by default).

## Quick Reference

### Authentication 🔐

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/auth/register` | POST | No | Register new user account |
| `/api/v1/auth/login` | POST | No | Login and receive JWT tokens |
| `/api/v1/auth/refresh` | POST | No | Refresh access token using refresh token |

### Voice Entry Management 🎙️

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/upload-transcribe-cleanup` | POST | Yes | **RECOMMENDED**: Complete workflow - upload, transcribe, and cleanup |
| `/api/v1/upload-and-transcribe` | POST | Yes | Upload audio and start transcription |
| `/api/v1/entries` | GET | Yes | **List all entries** (paginated, with status) |
| `/api/v1/entries/{id}` | GET | Yes | Get entry metadata with transcription |
| `/api/v1/entries/{id}/cleaned` | GET | Yes | List all cleaned entries for a voice entry |

**Note:** Manual workflow endpoints (separate upload/transcribe/cleanup) are also available. See `/docs` for details.

### Transcription & Cleanup 🤖

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/transcriptions/{id}` | GET | Yes | Get transcription status and text |
| `/api/v1/transcriptions/{id}/cleanup` | POST | Yes | Start LLM cleanup of transcription |
| `/api/v1/transcriptions/{id}/set-primary` | PUT | Yes | Set transcription as primary for entry |
| `/api/v1/cleaned-entries/{id}` | GET | Yes | Get cleaned text with analysis |

### Manual Workflow (Advanced) 🔧

For granular control, use separate endpoints:

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/upload` | POST | Yes | Upload audio file only |
| `/api/v1/entries/{id}/transcribe` | POST | Yes | Trigger transcription for uploaded entry |
| `/api/v1/entries/{id}/transcriptions` | GET | Yes | List all transcriptions for an entry |

### User Preferences ⚙️

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/user/preferences` | GET | Yes | Get current user's preferences |
| `/api/v1/user/preferences` | PUT | Yes | Update user preferences (e.g., preferred transcription language) |

### System 💚

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/health` | GET | No | Health check (includes DB status) |
| `/docs` | GET | No | Interactive API documentation (Swagger UI) |
| `/redoc` | GET | No | Alternative API documentation (ReDoc) |
| `/openapi.json` | GET | No | OpenAPI 3.0 specification |

## Quick Examples

### Authentication Workflow

**1. Register a new user:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "is_active": true,
  "created_at": "2025-11-10T12:00:00Z"
}
```

**2. Login to get tokens:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**3. Refresh access token:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

Response includes new `access_token` and `refresh_token`.

**Important**: Save your access token and include it in the `Authorization` header for all subsequent requests.

### Complete Workflow (Recommended)

**Note:** All examples below require authentication. Set your token first:
```bash
export ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Upload, transcribe, and cleanup in one request:**
```bash
curl -X POST "http://localhost:8000/api/v1/upload-transcribe-cleanup" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@recording.mp3;type=audio/mpeg" \
  -F "language=auto" \
  -F "entry_type=dream"
```

Response:
```json
{
  "entry_id": "550e8400-e29b-41d4-a716-446655440000",
  "transcription_id": "660e8400-e29b-41d4-a716-446655440001",
  "cleanup_id": "770e8400-e29b-41d4-a716-446655440002",
  "transcription_status": "processing",
  "cleanup_status": "pending",
  "message": "File uploaded, transcription and cleanup started"
}
```

This endpoint:
1. Uploads the audio file
2. Starts transcription (Whisper)
3. Starts cleanup (LLM) after transcription completes
4. Returns all IDs immediately

**Parameters:**
- `file` (required): MP3 or M4A audio file
- `language` (optional): Language code (`en`, `es`, `sl`) or `auto`. Default: `auto`
- `entry_type` (optional): Entry type (`dream`, `journal`, `meeting`, `note`). Default: `dream`

**Check cleanup status:**
```bash
curl "http://localhost:8000/api/v1/cleaned-entries/{cleanup_id}" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Returns cleaned text with theme and emotion analysis when complete.

### Upload and Transcribe Only

If you don't need LLM cleanup, use the simpler endpoint:

```bash
curl -X POST "http://localhost:8000/api/v1/upload-and-transcribe" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@recording.mp3;type=audio/mpeg" \
  -F "language=en" \
  -F "entry_type=journal"
```

Response includes `entry_id` and `transcription_id`. Transcription runs in the background.

**Get entry with transcription:**
```bash
curl "http://localhost:8000/api/v1/entries/{entry_id}" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Returns entry metadata including transcription status and text (when completed).

### List Entries

**Get paginated list of all entries:**
```bash
curl "http://localhost:8000/api/v1/entries?limit=20&offset=0" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Response:
```json
{
  "entries": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "original_filename": "dream_2025-11-15.m4a",
      "saved_filename": "550e8400-e29b_1731542400.m4a",
      "file_path": "/data/audio/2025-11-15/550e8400-e29b_1731542400.m4a",
      "entry_type": "dream",
      "duration_seconds": 125.5,
      "uploaded_at": "2025-11-15T03:15:00Z",
      "primary_transcription": {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "status": "completed",
        "language_code": "en",
        "error_message": null,
        "created_at": "2025-11-15T03:15:05Z"
      },
      "latest_cleaned_entry": {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "status": "COMPLETED",
        "cleaned_text_preview": "I dreamt I was flying over a vast ocean, the water sparkling beneath me in shades of turquoise and deep blue. There was a sense of freedom and weightlessness, as if I had no worries. In the dis...",
        "analysis": {
          "themes": ["flying", "freedom", "ocean"],
          "emotions": ["joy", "peace", "wonder"],
          "characters": [],
          "locations": ["ocean", "sky"]
        },
        "error_message": null,
        "created_at": "2025-11-15T03:15:20Z"
      }
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

**Query Parameters:**
- `limit` (optional): Number of entries to return (1-100, default: 20)
- `offset` (optional): Number of entries to skip for pagination (default: 0)
- `entry_type` (optional): Filter by type (`dream`, `journal`, `meeting`, `note`)

**Filter by entry type:**
```bash
curl "http://localhost:8000/api/v1/entries?entry_type=dream&limit=10" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Pagination example (page 2):**
```bash
curl "http://localhost:8000/api/v1/entries?limit=20&offset=20" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response Details:**
- Entries are ordered by `uploaded_at` DESC (newest first)
- Includes `duration_seconds` for each entry (audio length in seconds)
- Shows transcription status (no text content)
- Shows cleanup status with text preview and analysis:
  - `cleaned_text_preview`: First 200 characters of cleaned text
  - `analysis`: Structured analysis (themes, emotions, characters, locations)
- `primary_transcription`: Status of the main transcription (automatically set when first transcription completes)
- `latest_cleaned_entry`: Most recent LLM cleanup with preview and analysis (if available)

**Status Values:**
- Transcription: `"pending"`, `"processing"`, `"completed"`, `"failed"`
- Cleanup: `"PENDING"`, `"PROCESSING"`, `"COMPLETED"`, `"FAILED"`

### User Preferences

**Get user preferences:**
```bash
curl -X GET "http://localhost:8000/api/v1/user/preferences" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440001",
  "preferred_transcription_language": "auto",
  "created_at": "2025-11-21T12:00:00Z",
  "updated_at": "2025-11-21T12:00:00Z"
}
```

**Update preferred transcription language:**
```bash
curl -X PUT "http://localhost:8000/api/v1/user/preferences" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "preferred_transcription_language": "sl"
  }'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440001",
  "preferred_transcription_language": "sl",
  "created_at": "2025-11-21T12:00:00Z",
  "updated_at": "2025-11-21T13:30:00Z"
}
```

**Supported Language Codes:**
- `"auto"` - Automatic language detection (default)
- `"en"` - English
- `"es"` - Spanish
- `"sl"` - Slovenian
- `"de"` - German
- `"fr"` - French
- ...and 94 more languages supported by Whisper

**Language Fallback Behavior:**
When uploading audio files, the system determines the transcription language using this fallback chain:
1. **Request parameter** - If `language` is provided in the upload request
2. **User preference** - If user has saved a preferred language
3. **Auto-detection** - Falls back to `"auto"` if neither is set

This allows users to set a default language once and omit the `language` parameter in subsequent uploads.

### System

**Health check:**
```bash
curl "http://localhost:8000/health"
```