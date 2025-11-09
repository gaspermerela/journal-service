"""
SQLAlchemy models for the journal service.
"""
from app.models.voice_entry import VoiceEntry
from app.models.transcription import Transcription

__all__ = ["VoiceEntry", "Transcription"]
