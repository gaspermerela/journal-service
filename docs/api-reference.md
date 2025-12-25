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
| `/api/v1/upload-transcribe-cleanup` | POST | Yes | Complete workflow - upload, transcribe, and cleanup |
| `/api/v1/upload-and-transcribe` | POST | Yes | Upload audio and start transcription |
| `/api/v1/entries` | GET | Yes | List all entries (paginated, with status) |
| `/api/v1/entries/{id}` | GET | Yes | Get entry metadata with transcription |
| `/api/v1/entries/{id}/audio` | GET | Yes | Download audio file for entry |
| `/api/v1/entries/{id}/cleaned` | GET | Yes | List all cleaned entries for a voice entry |

**Note:** Manual workflow endpoints (separate upload/transcribe/cleanup) are also available. See Manual Workflow section. \
**Note:** TODO? It might be better to include cleaned transcriptions in `/api/v1/entries/{id}` endpoint.
### Transcription & Cleanup 🤖

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/transcriptions/{id}` | GET | Yes | Get transcription status and text |
| `/api/v1/transcriptions/{id}/cleanup` | POST | Yes | Start LLM cleanup of transcription |
| `/api/v1/transcriptions/{id}/set-primary` | PUT | Yes | Set transcription as primary for entry |
| `/api/v1/cleaned-entries/{id}` | GET | Yes | Get cleaned text and status |

### Manual Workflow (Advanced) 🔧

For granular control, use separate endpoints:

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/upload` | POST | Yes | Upload audio file only |
| `/api/v1/entries/{id}/transcribe` | POST | Yes | Trigger transcription for uploaded entry |
| `/api/v1/entries/{id}/transcriptions` | GET | Yes | List all transcriptions for an entry |

### Deletion Operations 🗑️

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/entries/{id}` | DELETE | Yes | Delete voice entry and all associated data (transcriptions, cleanups, syncs, audio file) |
| `/api/v1/transcriptions/{id}` | DELETE | Yes | Delete transcription and all cleaned entries (prevents deleting last transcription) |
| `/api/v1/cleaned-entries/{id}` | DELETE | Yes | Delete cleaned entry (no restrictions) |

**Important Notes:**
- All deletions require user ownership verification
- Entry deletion cascades to all child records (transcriptions, cleanups, notion syncs) and audio file
- Transcription deletion prevented if it's the only one for an entry
- Cleaned entry deletion has no restrictions

### User Preferences ⚙️

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/user/preferences` | GET | Yes | Get current user's preferences |
| `/api/v1/user/preferences` | PUT | Yes | Update user preferences (e.g., preferred transcription language) |

### Notion Integration 🔗

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/notion/configure` | POST | Yes | Configure Notion integration with API key and database ID |
| `/api/v1/notion/settings` | GET | Yes | Get current Notion integration settings |
| `/api/v1/notion/disconnect` | DELETE | Yes | Disconnect Notion integration and delete encrypted API key |
| `/api/v1/notion/sync/{entry_id}` | POST | Yes | Sync entry to Notion (creates or updates page) |
| `/api/v1/notion/sync/{sync_id}` | GET | Yes | Get sync operation status |
| `/api/v1/notion/syncs` | GET | Yes | List all sync records (paginated) |

**Key Features:**
- API keys are encrypted before storage using Fernet encryption
- Auto-sync triggers Notion sync after LLM cleanup completes (if enabled)
- Notion database must have required properties: Name (title), Date (date), Wake Time (rich_text)
- Sync operations are idempotent - re-syncing updates existing Notion page

### Models & Options 🤖

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/options` | GET | No | Get unified options (models + parameters) for transcription and LLM |
| `/api/v1/models/languages` | GET | No | List supported transcription languages |

### System 💚

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/health` | GET | No | Health check (includes DB status) |
| `/docs` | GET | No | Interactive API documentation (Swagger UI) |
| `/redoc` | GET | No | Alternative API documentation (ReDoc) |
| `/openapi.json` | GET | No | OpenAPI 3.0 specification |

## Endpoint Details

### Complete Workflow (Recommended)

**POST `/api/v1/upload-transcribe-cleanup`**

Upload, transcribe, and cleanup in one request. This endpoint:
1. Uploads the audio file
2. Starts transcription
3. Starts cleanup (LLM) after transcription completes
4. Returns all IDs immediately

**Parameters:**
- `file` (required): Audio file (MP3, M4A, WAV, etc.)
- `language` (optional): Language code (`en`, `es`, `sl`) or `auto`. Default: user preference → `auto`
- `entry_type` (optional): Entry type (`dream`, `journal`, `meeting`, `note`). Default: `dream`

**Transcription Parameters:**
- `transcription_provider` (optional): Provider to use (`groq`, `assemblyai`, `clarin-slovene-asr`). Default: configured provider
- `transcription_model` (optional): Model/variant (e.g., `whisper-large-v3`, `pyannote` for Slovenian ASR). Default: configured model
- `transcription_temperature` (optional): Transcription temperature (0.0-1.0). Default: 0.0
- `enable_diarization` (optional): Enable speaker identification. Default: false
- `speaker_count` (optional): Expected number of speakers (1-20). Default: auto-detect

**LLM Cleanup Parameters:**
- `llm_provider` (optional): Provider to use (`groq`, `runpod_llm_gams`). Default: configured provider
- `llm_model` (optional): LLM model (e.g., `llama-3.3-70b-versatile`, `GaMS-9B-Instruct`). Default: configured model
- `cleanup_temperature` (optional): LLM temperature (0.0-2.0, higher = more creative). Default: 0.0
- `cleanup_top_p` (optional): LLM nucleus sampling (0.0-1.0). Default: 0.0

**AI Parameters:**
- Parameters are **immutable** - saved at creation time and never changed.
- Use `/api/v1/options` endpoint to discover valid ranges for your configured providers
- Omitting parameters uses sensible defaults from configuration

**Response:**
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

### Upload and Transcribe Only

**POST `/api/v1/upload-and-transcribe`**

If you don't need LLM cleanup, use this simpler endpoint. Response includes `entry_id` and `transcription_id`. Transcription runs in the background.

**Parameters:**
- `file` (required): Audio file (MP3, M4A, WAV, etc.)
- `language` (optional): Language code or `auto`. Default: user preference → `auto`
- `entry_type` (optional): Entry type. Default: `dream`
- `transcription_provider` (optional): Provider (`groq`, `assemblyai`, `clarin-slovene-asr`). Default: configured provider
- `transcription_model` (optional): Model/variant to use. Default: configured model
- `transcription_temperature` (optional): Temperature (0.0-1.0). Default: 0.0
- `enable_diarization` (optional): Enable speaker identification. Default: false
- `speaker_count` (optional): Expected number of speakers. Default: auto-detect

### List Entries

**GET `/api/v1/entries`**

Get paginated list of all entries with transcription and cleanup status.

**Query Parameters:**
- `limit` (optional): Number of entries to return (1-100, default: 20)
- `offset` (optional): Number of entries to skip for pagination (default: 0)
- `entry_type` (optional): Filter by type (`dream`, `journal`, `meeting`, `note`)

**Response:**
```json
{
  "entries": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "original_filename": "dream_2025-11-15.m4a",
      "saved_filename": "550e8400-e29b_1731542400.m4a",
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
        "status": "completed",
        "cleaned_text_preview": "I dreamt I was flying over a vast ocean...",
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

**Response Details:**
- Entries ordered by `uploaded_at` DESC (newest first)
- Includes `duration_seconds` for each entry (audio length in seconds)
- Shows transcription status (no text content in list view)
- Shows cleanup status with text preview
- `primary_transcription`: Automatically set when first transcription completes
- `latest_cleaned_entry`: Most recent LLM cleanup with preview

**Status Values:**
- Transcription: `pending`, `processing`, `completed`, `failed`
- Cleanup: `pending`, `processing`, `completed`, `failed`

### Download Audio File

**GET `/api/v1/entries/{id}/audio`**

Download the audio file for an entry.

**Security:**
- Requires JWT authentication
- Users can only download their own audio files
- Returns 404 for both non-existent entries and unauthorized access (prevents leaking entry IDs)

**Technical Details:**
- Audio files are served in their stored format (WAV if preprocessing enabled, otherwise original format)
- When preprocessing is enabled (`ENABLE_AUDIO_PREPROCESSING=true`), files are 16kHz mono WAV
- When preprocessing is disabled (default for Groq transcription), files are in original upload format
- Supports range requests for seeking in audio players (`Accept-Ranges: bytes`)
- Files are cached for 1 hour with `immutable` directive
- Content-Disposition header set to `inline` for browser playback

**Response Headers:**
- `Content-Type`: `audio/wav` (preprocessed) or original MIME type
- `Accept-Ranges: bytes` - Enables seeking in audio players
- `Cache-Control: private, max-age=3600, immutable` - Caching for 1 hour
- `Content-Disposition: inline; filename="audio.{ext}"` - Play in browser

**Error Responses:**
- `403 Forbidden` - Missing or invalid authentication token
- `404 Not Found` - Entry doesn't exist, user doesn't own it, or file unavailable
- `422 Unprocessable Entity` - Invalid UUID format

### Delete Operations

**DELETE `/api/v1/entries/{id}`**

Delete a voice entry and all associated data (transcriptions, cleanups, notion syncs, audio file). Cascading deletion ensures no orphaned data. Operation is irreversible.

**DELETE `/api/v1/transcriptions/{id}`**

Delete a specific transcription and all associated cleaned entries. Cannot delete if it's the only transcription for an entry (returns 400 Bad Request).

**DELETE `/api/v1/cleaned-entries/{id}`**

Delete a cleaned entry. No restrictions - can delete any cleaned entry you own.

### User Preferences

**GET `/api/v1/user/preferences`**

Get current user's preferences.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440001",
  "preferred_transcription_language": "auto",
  "created_at": "2025-11-21T12:00:00Z",
  "updated_at": "2025-11-21T12:00:00Z"
}
```

**PUT `/api/v1/user/preferences`**

Update user preferences.

**Request Body:**
```json
{
  "preferred_transcription_language": "sl"
}
```

**Supported Language Codes:**
- `auto` - Automatic language detection (default)
- `en` - English, `es` - Spanish, `sl` - Slovenian, `de` - German, `fr` - French
- ...and 94 more languages supported by Whisper

**Language Fallback Behavior:**

When uploading audio files, the system determines the transcription language using this fallback chain:
1. **Request parameter** - If `language` is provided in the upload request
2. **User preference** - If user has saved a preferred language
3. **Auto-detection** - Falls back to `auto` if neither is set

### Models & Options

**GET `/api/v1/options`**

Get unified options (models + parameters) for transcription and LLM. This endpoint is **recommended** for discovering available models and parameter constraints.

**Response (example with Groq transcription + GaMS LLM):**
```json
{
  "transcription": {
    "provider": "groq",
    "available_providers": ["groq", "assemblyai", "clarin-slovene-asr", "noop"],
    "models": [
      {"id": "whisper-large-v3", "name": "Whisper Large v3"}
    ],
    "parameters": {
      "temperature": {
        "type": "float",
        "min": 0.0,
        "max": 1.0,
        "default": 0.0,
        "description": "Sampling temperature for transcription"
      }
    }
  },
  "llm": {
    "provider": "runpod_llm_gams",
    "available_providers": ["groq", "runpod_llm_gams", "noop"],
    "models": [
      {"id": "GaMS-9B-Instruct", "name": "GaMS 9B Instruct", "description": "Native Slovenian LLM. Best balance of quality and cost."}
    ],
    "parameters": {
      "temperature": {
        "type": "float",
        "min": 0.0,
        "max": 2.0,
        "default": 0.0,
        "description": "Sampling temperature (higher = more creative)"
      },
      "top_p": {
        "type": "float",
        "min": 0.0,
        "max": 1.0,
        "default": 0.0,
        "description": "Nucleus sampling threshold"
      }
    }
  }
}
```

**Available Providers:**

| Type | Providers                                                                     |
|------|-------------------------------------------------------------------------------|
| Transcription | `groq` (Whisper), `assemblyai`, `clarin-slovene-asr` (Slovenian)              |
| LLM Cleanup | `groq`, `runpod_llm_gams` (Slovenian GaMS)                          |

**Notes:**
- **No authentication required** - this endpoint is public
- **Dynamic parameters** - Parameter availability depends on configured providers
- **Per-request override** - Use `transcription_provider` and `llm_provider` in upload requests
- Set default providers via `DEFAULT_TRANSCRIPTION_PROVIDER` and `DEFAULT_LLM_PROVIDER` environment variables
- Use this endpoint to discover available models and valid parameter ranges before making upload requests

**GET `/api/v1/models/languages`**

List all supported transcription languages.

**Response:**
```json
{
  "languages": ["auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "...and 90+ more"],
  "count": 100
}
```

Both Whisper and Groq support 99+ languages plus auto-detection. Supported languages include all major world languages.

## Interactive Documentation

For complete, up-to-date API documentation with request/response schemas and the ability to test endpoints directly:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
