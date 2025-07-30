from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import json


class AudioSession(Base):
    """Model for audio processing sessions."""
    __tablename__ = "audio_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    processing_history = relationship("ProcessingHistory", back_populates="session")
    audio_files = relationship("AudioFile", back_populates="session")


class ProcessingHistory(Base):
    """Model for tracking audio processing operations."""
    __tablename__ = "processing_history"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("audio_sessions.session_id"), nullable=False)
    effect = Column(String, nullable=False)
    parameters = Column(Text)  # JSON string of effect parameters
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    samples_processed = Column(Integer, default=0)
    processing_time_ms = Column(Float, default=0.0)
    
    # Relationships
    session = relationship("AudioSession", back_populates="processing_history")
    
    def get_parameters(self) -> dict:
        """Get parameters as dictionary."""
        if self.parameters:
            return json.loads(self.parameters)
        return {}
    
    def set_parameters(self, params: dict):
        """Set parameters from dictionary."""
        self.parameters = json.dumps(params)


class AudioFile(Base):
    """Model for uploaded audio files."""
    __tablename__ = "audio_files"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("audio_sessions.session_id"), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    duration = Column(Float, default=0.0)  # Duration in seconds
    sample_rate = Column(Integer, default=44100)
    channels = Column(Integer, default=1)
    format = Column(String, default="wav")
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Audio analysis data
    rms_level = Column(Float, default=0.0)
    peak_level = Column(Float, default=0.0)
    dynamic_range = Column(Float, default=0.0)
    spectral_centroid = Column(Float, default=0.0)
    spectral_rolloff = Column(Float, default=0.0)
    
    # Relationships
    session = relationship("AudioSession", back_populates="audio_files")


class User(Base):
    """Model for user accounts."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # User preferences
    default_sample_rate = Column(Integer, default=44100)
    default_buffer_size = Column(Integer, default=44100)
    preferred_effects = Column(Text)  # JSON array of preferred effects


class EffectPreset(Base):
    """Model for saved effect presets."""
    __tablename__ = "effect_presets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    effect_type = Column(String, nullable=False)
    parameters = Column(Text, nullable=False)  # JSON string of parameters
    description = Column(Text)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def get_parameters(self) -> dict:
        """Get parameters as dictionary."""
        return json.loads(self.parameters)
    
    def set_parameters(self, params: dict):
        """Set parameters from dictionary."""
        self.parameters = json.dumps(params)


class AudioProject(Base):
    """Model for audio projects containing multiple sessions."""
    __tablename__ = "audio_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_archived = Column(Boolean, default=False)
    
    # Project settings
    sample_rate = Column(Integer, default=44100)
    bit_depth = Column(Integer, default=16)
    channels = Column(Integer, default=2)
    
    # Relationships
    sessions = relationship("AudioSession", secondary="project_sessions")


class ProjectSession(Base):
    """Association table for projects and sessions."""
    __tablename__ = "project_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("audio_projects.id"), nullable=False)
    session_id = Column(String, ForeignKey("audio_sessions.session_id"), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    order_index = Column(Integer, default=0)  # For ordering sessions in project 