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

Claude should select popular, well-supported Python libraries.

**Mandatory constraints:**

- ✅ Database: PostgreSQL
- ✅ ORM: SQLAlchemy
- ✅ Should support migrations
- ✅ Should support structured logging
- ✅ Environment config: `.env` support via `python-dotenv` or similar
- ✅ Containerization: Docker (Dockerfile + docker-compose)

---

## 📂 File Storage

- Audio files are saved to `/data/audio/` with format ` /data/audio/YYYY-MM-DD/`
- Base path should be configurable in `.env`
- Files should be renamed to UUID + timestamp
- Subfolders by date (useful for scale and transparency)
- Original filename preserved in metadata

---

## 🗃️ Database

###
- Database connection should be configurable in `.env`

### Schema
**Table: `dream_entries`**
- UUID 
- Original file name received
- Final saved filename (UUID-based)
- Absolute path of saved file
- Time of upload

---

## 🪵 Logging

Use structured logging for:

- Incoming requests (IP, filename, timestamp)
- File storage (success/failure)
- DB operations (success/failure)
- Unhandled errors with stack traces

Logging should be text based for now.

Log level should be configurable via `.env`

Logging of other information on case by case basis.

---

## 🧪 Tests

- ✅ Unit test: file saving logic
- ✅ Integration test: `/upload` endpoint (using test DB)

---

## 🐳 Dockerization

- Provide a `Dockerfile` for the app
- Provide a `docker-compose.yml` with:
  - App service
  - PostgreSQL service
  - Volume mount for `/data/audio`
- Include `.env.example` file

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
During AI based and manual development, we must maintain detailed documentation 
`docs/` directory. It should be structured in multiple `.md` files, for example (but not necessarily like this):
- overview.md
- endpoints.md
- database-schema.md
- logging.md
- future-features.md
-  changelog.md
