"""
Database layer. Every row here is created from real, live data returned by
the GitHub API or produced by the agent pipeline at run time - nothing is
seeded or hardcoded.
"""
import datetime as dt
import enum

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Enum, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ScanStatus(str, enum.Enum):
    pending = "pending"
    analyzing_diff = "analyzing_diff"
    matching_docs = "matching_docs"
    drafting_patch = "drafting_patch"
    completed = "completed"
    failed = "failed"


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String, nullable=False)
    name = Column(String, nullable=False)
    full_name = Column(String, unique=True, nullable=False)
    default_branch = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    github_token = Column(String, nullable=True)  # per-repo token override, optional
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    scans = relationship("Scan", back_populates="repository", cascade="all, delete-orphan")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    commit_sha = Column(String, nullable=False)
    commit_message = Column(Text, nullable=True)
    status = Column(Enum(ScanStatus), default=ScanStatus.pending)
    error_message = Column(Text, nullable=True)
    diff_analysis = Column(Text, nullable=True)      # output of Agent 1
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    repository = relationship("Repository", back_populates="scans")
    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    doc_path = Column(String, nullable=False)
    severity = Column(String, nullable=False)   # low | medium | high - decided by the agent
    summary = Column(Text, nullable=False)
    suggested_patch = Column(Text, nullable=True)  # markdown produced by Agent 3
    pr_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    scan = relationship("Scan", back_populates="findings")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
