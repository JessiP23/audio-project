"""
SQLAlchemy database models for the Audio Processing Backend.
Defines the database schema for audio sessions, files, and processing history.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
import json
from typing import Dict, Any, Optional

from app.db.session import Base


class AudioSession(Base):
    """Model for audio processing sessions."""
    __tablename__ = "audio_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    user_id = Column(String(255), nullable=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Session metadata
    sample_rate = Column(Integer, default=44100)
    buffer_size = Column(Integer, default=44100)
    total_samples_processed = Column(Integer, default=0)
    
    # Relationships
    processing_history = relationship("ProcessingHistory", back_populates="session", cascade="all, delete-orphan")
    audio_files = relationship("AudioFile", back_populates="session", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_session_user', 'user_id'),
        Index('idx_session_created', 'created_at'),
    )


class ProcessingHistory(Base):
    """Model for tracking audio processing operations."""
    __tablename__ = "processing_history"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("audio_sessions.session_id"), nullable=False)
    effect = Column(String(100), nullable=False)
    parameters = Column(Text)  # JSON string of effect parameters
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    samples_processed = Column(Integer, default=0)
    processing_time_ms = Column(Float, default=0.0)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    session = relationship("AudioSession", back_populates="processing_history")
    
    # Indexes
    __table_args__ = (
        Index('idx_history_session', 'session_id'),
        Index('idx_history_effect', 'effect'),
        Index('idx_history_processed_at', 'processed_at'),
    )
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get parameters as dictionary."""
        if self.parameters:
            try:
                return json.loads(self.parameters)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_parameters(self, params: Dict[str, Any]) -> None:
        """Set parameters from dictionary."""
        self.parameters = json.dumps(params)


class AudioFile(Base):
    """Model for uploaded audio files."""
    __tablename__ = "audio_files"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("audio_sessions.session_id"), nullable=False)
    file_id = Column(String(255), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    duration = Column(Float, default=0.0)  # Duration in seconds
    sample_rate = Column(Integer, default=44100)
    channels = Column(Integer, default=1)
    format = Column(String(10), default="wav")
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Audio analysis data
    rms_level = Column(Float, default=0.0)
    peak_level = Column(Float, default=0.0)
    dynamic_range = Column(Float, default=0.0)
    spectral_centroid = Column(Float, default=0.0)
    spectral_rolloff = Column(Float, default=0.0)
    zero_crossing_rate = Column(Float, default=0.0)
    
    # File metadata
    tags = Column(Text)  # JSON array of tags
    file_metadata = Column(Text)  # JSON object of additional metadata
    
    # Relationships
    session = relationship("AudioSession", back_populates="audio_files")
    
    # Indexes
    __table_args__ = (
        Index('idx_file_session', 'session_id'),
        Index('idx_file_uploaded', 'uploaded_at'),
        Index('idx_file_format', 'format'),
    )
    
    def get_tags(self) -> list:
        """Get tags as list."""
        if self.tags:
            try:
                return json.loads(self.tags)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_tags(self, tags: list) -> None:
        """Set tags from list."""
        self.tags = json.dumps(tags)
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata as dictionary."""
        if self.file_metadata:
            try:
                return json.loads(self.file_metadata)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set metadata from dictionary."""
        self.file_metadata = json.dumps(metadata)


class EffectPreset(Base):
    """Model for saved effect presets."""
    __tablename__ = "effect_presets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    effect_type = Column(String(100), nullable=False)
    parameters = Column(Text, nullable=False)  # JSON string of parameters
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_preset_user', 'user_id'),
        Index('idx_preset_type', 'effect_type'),
        Index('idx_preset_public', 'is_public'),
    )
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get parameters as dictionary."""
        try:
            return json.loads(self.parameters)
        except json.JSONDecodeError:
            return {}
    
    def set_parameters(self, params: Dict[str, Any]) -> None:
        """Set parameters from dictionary."""
        self.parameters = json.dumps(params)


class AudioProject(Base):
    """Model for audio projects containing multiple sessions."""
    __tablename__ = "audio_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_archived = Column(Boolean, default=False)
    
    # Project settings
    sample_rate = Column(Integer, default=44100)
    bit_depth = Column(Integer, default=16)
    channels = Column(Integer, default=2)
    
    # Indexes
    __table_args__ = (
        Index('idx_project_user', 'user_id'),
        Index('idx_project_archived', 'is_archived'),
    )


class ProjectSession(Base):
    """Association table for projects and sessions."""
    __tablename__ = "project_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("audio_projects.id"), nullable=False)
    session_id = Column(String(255), ForeignKey("audio_sessions.session_id"), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    order_index = Column(Integer, default=0)  # For ordering sessions in project
    
    # Indexes
    __table_args__ = (
        Index('idx_project_session_project', 'project_id'),
        Index('idx_project_session_order', 'project_id', 'order_index'),
    ) 