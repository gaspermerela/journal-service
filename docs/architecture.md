# Architecture

High-level design decisions and trade-offs.

## How It Works

### Upload Flow

```
1. User authenticates (JWT)
2. Client POSTs audio file (MP3, M4A, WAV, etc.)
3. Validate file type + size
4. Generate UUID + timestamp filename
5. Save audio file to disk
6. Preprocess audio (16kHz mono WAV, noise reduction, normalization)
7. Calculate audio duration
8. Create database record
9. Encrypt audio file (envelope encryption)
   - Create/reuse DEK for this VoiceEntry
   - Delete original unencrypted file
10. Start background transcription (provider-configurable)
11. Return entry metadata + transcription_id
```

**Cleanup mechanism:** If database write fails, saved file is deleted automatically. No orphaned files.
**Encryption:** All audio files are encrypted. Frontend receives decrypted audio via the download endpoint.

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

## API Endpoints Overview

The service provides REST endpoints across 9 functional areas:

1. **Authentication** - Registration, login, token refresh
2. **Upload** - File upload with optional transcription and cleanup
3. **Entries** - CRUD operations for voice entries (list, get, download audio, delete)
4. **Transcriptions** - Transcription management with set-primary and deletion
5. **Cleanup** - LLM cleanup with set-primary and deletion
6. **Notion Integration** - Configuration, sync, and status tracking
7. **User Preferences** - Get and update user settings
8. **Models/Options** - Discover available models, parameters, and languages
9. **Health** - Service health check

**Key Features:**
- **Unified options endpoint** - `/api/v1/options` for dynamic parameter discovery based on configured providers
- **Per-request provider selection** - Override default transcription or LLM provider per request
- **Soft deletion prevention** - Cannot delete last transcription for an entry
- **Cascading deletes** - Entry deletion removes all child records and audio file
- **Idempotent Notion sync** - Re-syncing updates existing Notion page
- **Immutable AI parameters** - Parameters saved at creation time for auditability

## Security & GDPR Compliance

### Envelope Encryption

The service implements **envelope encryption** for GDPR-compliant data protection.

**Encryption is always enabled** - there is no user toggle. The application fails at startup if the encryption service is unavailable. All audio files, transcriptions, and cleaned entries are encrypted.

```
Master Key → KEK (per-user) → DEK (per-VoiceEntry) → Data
```

**How it works:**
- Each VoiceEntry gets a unique **Data Encryption Key (DEK)**
- The DEK encrypts all related data: audio file, transcriptions, cleaned entries
- DEKs are encrypted with a **Key Encryption Key (KEK)** derived per-user
- One DEK per VoiceEntry = fewer key operations, simpler deletion

**GDPR Cryptographic Erasure:**
- Destroying a DEK makes all associated data permanently unrecoverable
- No need to find and delete scattered data - destroy the key, data is gone
- Audit trail maintained (`deleted_at` timestamp on DEK record)

**Current Implementation: Local KEK Provider**
- KEK derived from master key + user ID using HKDF
- AES-256-GCM for all encryption
- Suitable for single-server deployments

**Future: AWS KMS Integration**
- KEK provider abstraction allows seamless upgrade to AWS KMS
- Per-user KMS keys for hardware-backed security
- Key rotation support built into the design
- `encryption_version` field tracks provider for migration

### Backup Strategy for GDPR Compliance

**Critical:** The `data_encryption_keys` table must be **excluded from regular database backups**.

**Why:**
- DEKs are the secret that unlocks encrypted data
- If DEKs are backed up, restoring a backup resurrects deleted data
- This violates GDPR's "right to erasure" - user data must stay deleted

**Recommended approach:**
```
Main Database (PostgreSQL)
├── All tables EXCEPT data_encryption_keys  →  Regular backups
└── data_encryption_keys table              →  NO backup, use replication instead
```

**How to handle DEK durability without backup:**
1. **PostgreSQL streaming replication** - DEKs replicated to standby in real-time
2. **Separate DEK storage** - Small table, can use dedicated highly-available storage
3. **Accept risk for MVP** - Single server, if disk dies, all data is lost anyway

**What happens on restore:**
- Backup restored → encrypted data exists but no DEKs (or don't restore data with missing DEKs)
- Encrypted data without DEK = unreadable garbage
- GDPR deletion is preserved - data cannot be recovered

### Authentication

- **JWT-based** with access and refresh tokens
- User data isolation enforced at database query level
- All queries automatically scoped to `user_id`

## Current Limitations

- No rate limiting per user (handled on server level - nginx)
- No batch operations (deletion, sync)
- Single server only (local disk storage)
- No webhook support for async operation completion
- No graceful shutdown (background tasks may be killed mid-processing)

## Tech Stack

**Core:**
- **FastAPI:** Async + auto OpenAPI docs
- **PostgreSQL:** Primary database
- **SQLAlchemy:** Async ORM
- **JWT:** Token-based auth
- **Docker:** Consistent deployment
- **Pytest:** Testing

**Transcription Providers:**
- **Groq:** Cloud Whisper API (default, 99+ languages)
- **AssemblyAI:** Cloud ASR with speaker diarization
- **Slovenian ASR:** RunPod serverless with PROTOVERB model (3 diarization variants)

**LLM Cleanup Providers:**
- **Groq:** Cloud LLM API (LLaMA models)
- **Ollama:** Local LLM (llama3.2:3b default)
- **GaMS:** RunPod serverless with native Slovenian LLM (GaMS-9B-Instruct)

**Audio Processing:**
- **ffmpeg:** Audio preprocessing (16kHz mono, noise reduction, normalization)
- **mutagen:** Audio duration and format detection

## Testing

Tests organized by type in subdirectories:

- **`tests/unit/`** - Business logic (no DB/external deps)
- **`tests/integration/`** - API routes + test database
- **`tests/e2e/`** - Full workflows with real services (marked with `@pytest.mark.e2e_real`)

## Provider Configuration

### Transcription Providers

**Default provider:** Set via `TRANSCRIPTION_PROVIDER` (default: `groq`)

| Provider | Required Settings | Optional Settings |
|----------|-------------------|-------------------|
| `groq` | `GROQ_API_KEY` | `GROQ_TRANSCRIPTION_MODEL` (default: `whisper-large-v3`) |
| `assemblyai` | `ASSEMBLYAI_API_KEY` | `ASSEMBLYAI_MODEL`, `ASSEMBLYAI_POLL_INTERVAL`, `ASSEMBLYAI_TIMEOUT` |
| `clarin-slovene-asr` | `RUNPOD_API_KEY` + at least one endpoint | See below |

**Slovenian ASR Endpoints** (RunPod):
```bash
SLOVENE_ASR_NFA_ENDPOINT_ID=xxx      # NeMo + NFA alignment
SLOVENE_ASR_MMS_ENDPOINT_ID=xxx      # NeMo + MMS alignment
SLOVENE_ASR_PYANNOTE_ENDPOINT_ID=xxx # pyannote 3.1 (best quality)
```

### LLM Cleanup Providers

**Default provider:** Set via `LLM_PROVIDER` (default: `groq`)

| Provider | Required Settings | Optional Settings |
|----------|-------------------|-------------------|
| `groq` | `GROQ_API_KEY` | `GROQ_LLM_MODEL` (default: `meta-llama/llama-4-maverick-17b-128e-instruct`) |
| `ollama` | None | `OLLAMA_BASE_URL` (default: `http://localhost:11434`), `OLLAMA_MODEL` |
| `runpod_llm_gams` | `RUNPOD_API_KEY`, `RUNPOD_LLM_GAMS_ENDPOINT_ID` | See below |

**GaMS LLM Settings** (RunPod):
```bash
RUNPOD_LLM_GAMS_ENDPOINT_ID=xxx        # Required: RunPod endpoint
RUNPOD_LLM_GAMS_MODEL=GaMS-9B-Instruct # Model variant
RUNPOD_LLM_GAMS_TIMEOUT=120            # Request timeout (seconds)
RUNPOD_LLM_GAMS_MAX_RETRIES=3          # Retry attempts
RUNPOD_LLM_GAMS_DEFAULT_TEMPERATURE=0.3
RUNPOD_LLM_GAMS_DEFAULT_TOP_P=0.9
RUNPOD_LLM_GAMS_MAX_TOKENS=2048
```

### Core Settings

```bash
# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USER=journal_user
DATABASE_PASSWORD=your_password

# Authentication
JWT_SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_DAYS=7
REFRESH_TOKEN_EXPIRE_DAYS=30

# Storage
AUDIO_STORAGE_PATH=/app/data/audio
MAX_FILE_SIZE_MB=100

# Encryption (required)
ENCRYPTION_MASTER_KEY=your-32-byte-key-base64

# Logging
LOG_LEVEL=INFO
SQLALCHEMY_LOG_LEVEL=WARNING
```

See `app/config.py` for the complete list of settings with defaults.