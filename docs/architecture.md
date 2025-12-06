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
6. Preprocess audio (16kHz mono WAV) - only for self-hosted transcription
7. Calculate audio duration
8. Create database record
9. Encrypt audio file (envelope encryption)
   - Create/reuse DEK for this VoiceEntry
   - Delete original unencrypted file
10. Start background transcription (Whisper)
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
- **Unified options endpoint** - `/api/v1/options` for dynamic parameter discovery, 
depending on what we are running (local whisper or groq for transcription, local ollama or groq for cleanup)
- **Soft deletion prevention** - Cannot delete last transcription for an entry
- **Cascading deletes** - Entry deletion removes all child records and audio file
- **Idempotent Notion sync** - Re-syncing updates existing Notion page
- **Immutable AI parameters** - Parameters saved at creation time for auditability

## Security & GDPR Compliance

### Envelope Encryption

The service implements **envelope encryption** for GDPR-compliant data protection.

**Encryption is always enabled** - there is no user toggle. The application fails at startup if the encryption service is unavailable. All audio files, transcriptions, and cleaned entries (including analysis) are encrypted.

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