# backend/app/models.py
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Float, Boolean
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .db import Base
import json

def JsonColumn():
    # Use Text to stay compatible; we'll store JSON-serialized strings
    return Column(Text, default="{}")

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    password_hash = Column(String)
    role = Column(String, default="recruiter")  # "admin" | "recruiter" | "student" -- see backend/app/auth.py
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ResumeUpload(Base):
    __tablename__ = "resume_uploads"
    id = Column(String, primary_key=True)  # uuid
    user_id = Column(String, nullable=True)
    file_name = Column(String)
    file_path = Column(String)
    status = Column(String, default="uploaded")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Resume(Base):
    __tablename__ = "resumes"
    id = Column(String, primary_key=True)  # uuid, same as upload id
    upload_id = Column(String, ForeignKey("resume_uploads.id"))
    raw_text = Column(Text)
    contact_info = JsonColumn()
    summary = Column(Text, nullable=True)
    education = JsonColumn()
    skills = JsonColumn()
    experience = JsonColumn()
    projects = JsonColumn()
    certifications = JsonColumn()
    achievements = JsonColumn()
    formatting = JsonColumn()
    overall_score = Column(Float, default=0)  # V2 engine returns a normalized float (e.g. 84.7), not an int
    scoring_version = Column(String, nullable=True)
    score_timestamp = Column(DateTime(timezone=True), nullable=True)
    scoring_config_version = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Without these, `resume.buckets` / `resume.mistakes` raise AttributeError, which
    # build_resume_export_rows() was silently swallowing via a bare `except:` -- exports
    # always had empty bucket columns as a result. See CLAUDE.md proactive-fix rules.
    buckets = relationship("ResumeBucket", backref="resume", cascade="all, delete-orphan")
    mistakes = relationship("ResumeMistake", backref="resume", cascade="all, delete-orphan")

class ResumeBucket(Base):
    __tablename__ = "resume_buckets"
    id = Column(String, primary_key=True)
    resume_id = Column(String, ForeignKey("resumes.id"))
    bucket_name = Column(String)
    score = Column(Float)
    max_score = Column(Float)
    weight = Column(Float)
    weighted_score = Column(Float, nullable=True)

class ResumeMistake(Base):
    __tablename__ = "resume_mistakes"
    id = Column(String, primary_key=True)
    resume_id = Column(String, ForeignKey("resumes.id"))
    category = Column(String)
    mistake = Column(String)
    feedback = Column(Text)
    section = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    criterion = Column(String, nullable=True)
    finding_type = Column(String, nullable=True)
    value = Column(String, nullable=True)
    expected = Column(String, nullable=True)
    impact = Column(Integer, nullable=True)
