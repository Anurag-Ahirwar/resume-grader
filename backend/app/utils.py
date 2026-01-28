# backend/app/utils.py
from pathlib import Path
import json

def list_uploaded_files(upload_dir: Path):
    return [p.name for p in upload_dir.glob("*.pdf")]
