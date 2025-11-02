# Changelog

All notable changes to the AI Journal Backend Service will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Audio transcription using Whisper model
- LLM-based text cleanup
- Notion integration for synced entries

## [0.1.0] - 2025-11-02

Initial release - Phase 1 complete. A backend foundation for voice-based journaling with architecture for future AI features.

### Added

**Core Features**
- MP3 audio upload endpoint with validation (type, size)
- Entry retrieval by UUID
- Health check with database connectivity
- UUID-based file storage with date-organized directories

**Database**
- PostgreSQL schema with `dream_entries` table
- Alembic migrations for schema management
- SQLAlchemy 2.0 async ORM

**Testing**
- Comprehensive test suite with ~85% coverage)
- Unit, integration, and end-to-end test coverage
- Test database isolation

**Deployment**
- Two-step rsync-based deployment pipeline (`deploy.sh`, `run.sh`)

**Documentation**
- Technical documentation (`/docs` directory)
- API documentation (Swagger UI, ReDoc)
- Setup, testing, deployment, and architecture guides
- CONTRIBUTING.md and MIT License

### Known Limitations
- No authentication
- No rate limiting
- No file retrieval (only metadata)
- No deletion
- Single server only