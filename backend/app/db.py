# backend/app/db.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Using SQLite for local dev. Path: C:\resume-grader\resume_grader.db
SQLITE_URL = "sqlite:///./resume_grader.db"

engine = create_engine(
    SQLITE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Additive columns introduced by the V2 scoring engine. Applied via PRAGMA-checked
# ALTER TABLE instead of a full Alembic migration (see V2 execution plan design notes) -
# safe to run repeatedly and never touches existing data.
_V2_COLUMNS = {
    "resumes": [
        ("scoring_version", "VARCHAR"),
        ("score_timestamp", "DATETIME"),
        ("scoring_config_version", "VARCHAR"),
    ],
    "resume_buckets": [
        ("weighted_score", "FLOAT"),
    ],
    "resume_mistakes": [
        ("severity", "VARCHAR"),
        ("criterion", "VARCHAR"),
        ("finding_type", "VARCHAR"),
        ("value", "VARCHAR"),
        ("expected", "VARCHAR"),
        ("impact", "INTEGER"),
    ],
}


def ensure_columns():
    """Add any missing V2 columns to existing SQLite tables without dropping data.
    No-op for a table that doesn't exist yet (create_all handles fresh tables)."""
    with engine.connect() as conn:
        existing_tables = {row[0] for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))}
        for table, columns in _V2_COLUMNS.items():
            if table not in existing_tables:
                continue
            existing_columns = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
            for column_name, column_type in columns:
                if column_name not in existing_columns:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_type}"))
        conn.commit()
