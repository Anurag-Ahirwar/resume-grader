# tools/inspect_db.py
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "resume_grader.db"

if not DB_PATH.exists():
    print(f"DB not found at {DB_PATH}")
    raise SystemExit(1)

conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

print("=== Resume rows ===")
for r in cur.execute("SELECT id, overall_score FROM resumes"):
    print(r)

print("\n=== Buckets ===")
for r in cur.execute("SELECT id, resume_id, bucket_name, score FROM resume_buckets"):
    print(r)

print("\n=== Mistakes (sample) ===")
for r in cur.execute("SELECT mistake, feedback FROM resume_mistakes LIMIT 10"):
    print(r)

conn.close()
