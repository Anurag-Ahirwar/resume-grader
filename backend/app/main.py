# backend/app/main.py
from sqlalchemy.orm import joinedload

from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Path as FastAPIPath, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Optional
from uuid import uuid4
from pathlib import Path
import shutil
import json
import uuid
import csv
import io
import re
import pandas as pd
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime, timezone

from parser_engine.parser import parse_pdf_to_text
from parser_engine.extractor import extract_all
from parser_engine.scoring import score_resume

from backend.app.db import SessionLocal
from backend.app import models
from backend.app.db import engine, ensure_columns
from backend.app.models import Base
from backend.app.auth import Role, get_current_user, require_role, create_access_token, verify_password

from parser_engine.report_engine import generate_resume_report

# ---------------------------------------------------
# Setup
# ---------------------------------------------------

app = FastAPI(title="Resume Grader API")

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

Base.metadata.create_all(bind=engine)
ensure_columns()


class UploadResponse(BaseModel):
    upload_ids: List[str]


def _scope_to_own_resumes(query, current_user: models.User):
    """Students only ever see resumes tied to an upload they own. Recruiters/Admins see everything."""
    if current_user.role == Role.STUDENT:
        query = query.join(
            models.ResumeUpload, models.Resume.upload_id == models.ResumeUpload.id
        ).filter(models.ResumeUpload.user_id == current_user.id)
    return query


# ---------------------------------------------------
# Health Check
# ---------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------
# Auth
# ---------------------------------------------------

@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    try:
        user = db.query(models.User).filter_by(email=form_data.username.strip().lower()).first()
    finally:
        db.close()

    if not user or not user.is_active or not verify_password(form_data.password, user.password_hash):
        # Same generic message either way -- don't reveal whether the account exists.
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token = create_access_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "name": user.name,
        "email": user.email,
    }


@app.get("/auth/me")
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
    }


# ---------------------------------------------------
# Upload Resumes
# ---------------------------------------------------

@app.post("/resumes/upload", response_model=UploadResponse)
async def upload_resumes(
    files: List[UploadFile] = File(...),
    current_user: models.User = Depends(get_current_user),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    upload_ids = []

    db = SessionLocal()
    try:
        for f in files:
            if not f.filename.lower().endswith(".pdf"):
                continue

            uid = str(uuid4())
            dest = UPLOAD_DIR / f"{uid}.pdf"

            with dest.open("wb") as out_file:
                shutil.copyfileobj(f.file, out_file)

            # Create the ResumeUpload row immediately (previously only created at process
            # time) so ownership can be tagged right away for Student-scoped access.
            db.add(models.ResumeUpload(
                id=uid,
                user_id=current_user.id,
                file_name=f.filename,
                file_path=str(dest),
                status="uploaded",
            ))

            upload_ids.append(uid)

            try:
                await f.close()
            except:
                pass

        db.commit()
    finally:
        db.close()

    return {"upload_ids": upload_ids}


# ---------------------------------------------------
# Upload CSV with Google Drive Links
# ---------------------------------------------------

@app.post("/resumes/upload-csv")
async def upload_csv_with_gdrive_links(
    file: UploadFile = File(...),
    current_user: models.User = Depends(require_role(Role.ADMIN, Role.RECRUITER)),
):
    """
    Upload CSV file containing Google Drive links to resumes.
    
    CSV Format (only resume_link column required):
        resume_link
        https://drive.google.com/file/d/FILE_ID/view
        https://drive.google.com/file/d/FILE_ID2/view
    
    Returns:
        - total: Number of rows in CSV
        - successful: Number successfully downloaded and saved
        - failed: Number that failed
        - results: Detailed results for each resume
    """
    from backend.app.utils.gdrive_downloader import download_from_gdrive, validate_gdrive_link
    import pandas as pd
    import io
    
    # Validate file type
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    try:
        # Read CSV content
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")
    
    # Validate required column
    if 'resume_link' not in df.columns:
        raise HTTPException(
            status_code=400,
            detail="CSV must have 'resume_link' column. Found columns: " + ", ".join(df.columns)
        )
    
    # Limit batch size
    MAX_BATCH_SIZE = 200
    if len(df) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Too many resumes. Maximum: {MAX_BATCH_SIZE}, Found: {len(df)}"
        )
    
    # Process each row
    results = []
    upload_ids = []
    
    for idx, row in df.iterrows():
        link = row.get('resume_link', '').strip()
        row_num = idx + 1
        
        try:
            # Validate link format
            is_valid, error_msg = validate_gdrive_link(link)
            if not is_valid:
                results.append({
                    'row': row_num,
                    'link': link[:50] + '...' if len(link) > 50 else link,
                    'status': 'failed',
                    'error': error_msg
                })
                continue
            
            # Download PDF from Google Drive
            pdf_content = download_from_gdrive(link, timeout=60)
            
            # Generate unique ID
            uid = str(uuid4())
            
            # Save PDF to uploads folder
            dest = UPLOAD_DIR / f"{uid}.pdf"
            dest.write_bytes(pdf_content)

            db = SessionLocal()
            try:
                db.add(models.ResumeUpload(
                    id=uid,
                    user_id=current_user.id,
                    file_name=f"{uid}.pdf",
                    file_path=str(dest),
                    status="uploaded",
                ))
                db.commit()
            finally:
                db.close()

            upload_ids.append(uid)
            
            results.append({
                'row': row_num,
                'link': link[:50] + '...' if len(link) > 50 else link,
                'upload_id': uid,
                'status': 'success',
                'size_kb': len(pdf_content) // 1024
            })
            
        except Exception as e:
            error_msg = str(e)
            # Simplify common error messages
            if "Cannot access file" in error_msg:
                error_msg = "File is private or link is invalid. Ensure 'Anyone with link' can view."
            elif "Not a valid PDF" in error_msg:
                error_msg = "Downloaded file is not a PDF. Make sure link points to PDF, not Doc/Sheet."
            elif "File too large" in error_msg:
                error_msg = error_msg  # Keep size info
            elif "timeout" in error_msg.lower():
                error_msg = "Download timeout. File may be too large or connection slow."
            
            results.append({
                'row': row_num,
                'link': link[:50] + '...' if len(link) > 50 else link,
                'status': 'failed',
                'error': error_msg
            })
    
    # Summary
    successful_count = len([r for r in results if r['status'] == 'success'])
    failed_count = len([r for r in results if r['status'] == 'failed'])
    
    return {
        "total": len(df),
        "successful": successful_count,
        "failed": failed_count,
        "upload_ids": upload_ids,
        "results": results
    }


# ---------------------------------------------------
# Debug: Parse PDF
# ---------------------------------------------------

@app.post("/debug/parse-pdf")
async def debug_parse_pdf(
    upload_id: str = Body(..., embed=True),
    current_user: models.User = Depends(require_role(Role.ADMIN)),
):
    pdf_path = UPLOAD_DIR / f"{upload_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(404, "upload_id not found")

    raw_text, diagnostics = parse_pdf_to_text(pdf_path)

    return {
        "upload_id": upload_id,
        "diagnostics": diagnostics,
        "raw_text_preview": raw_text[:400],
        "raw_text_full_length": len(raw_text)
    }


# ---------------------------------------------------
# Debug: Extract structured fields
# ---------------------------------------------------

@app.post("/debug/extract-fields")
async def debug_extract_fields(
    upload_id: str = Body(..., embed=True),
    current_user: models.User = Depends(require_role(Role.ADMIN)),
):
    pdf_path = UPLOAD_DIR / f"{upload_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(404, "upload_id not found")

    raw_text, diagnostics = parse_pdf_to_text(pdf_path)
    extracted = extract_all(raw_text)

    # Add debug info: show email-related text snippets
    email_debug = {}
    if "akshita" in raw_text.lower() or "akshitajain" in raw_text.lower():
        # Find text around potential email
        email_pattern = r'[a-zA-Z0-9._+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+'
        email_matches = re.findall(email_pattern, raw_text)
        email_debug["regex_matches"] = email_matches
        # Show first 200 chars where email might be
        email_index = raw_text.lower().find("akshita")
        if email_index >= 0:
            email_debug["text_around_name"] = raw_text[max(0, email_index-50):email_index+200]

    return {
        "upload_id": upload_id,
        "diagnostics": diagnostics,
        "extracted": extracted,
        "debug_email": email_debug if email_debug else None,
        "raw_text_preview": raw_text[:500]  # First 500 chars for debugging
    }


# ---------------------------------------------------
# PROCESS RESUME (Main Pipeline)
# ---------------------------------------------------

@app.post("/resumes/process/{upload_id}")
async def process_resume(
    upload_id: str = FastAPIPath(...),
    current_user: models.User = Depends(get_current_user),
):
    pdf_path = UPLOAD_DIR / f"{upload_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(404, "upload_id not found")

    if current_user.role == Role.STUDENT:
        db = SessionLocal()
        try:
            upload_row = db.query(models.ResumeUpload).filter_by(id=upload_id).first()
        finally:
            db.close()
        if not upload_row or upload_row.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You do not have permission to perform this action.")

    # Parse
    raw_text, diagnostics = parse_pdf_to_text(pdf_path)

    # Extract from text
    extracted = extract_all(raw_text)

    # Enrich contact info with clickable links from PDF (GitHub / LinkedIn)
    links = diagnostics.get("links", []) if isinstance(diagnostics, dict) else []
    if links:
        contact = extracted.get("contact", {}) or {}
        for url in links:
            url_lower = url.lower()
            if "linkedin.com" in url_lower and not contact.get("linkedin"):
                contact["linkedin"] = url
            if "github.com" in url_lower and not contact.get("github"):
                contact["github"] = url
        extracted["contact"] = contact

    # Attach diagnostics for scoring / debugging
    extracted["_diagnostics"] = diagnostics

    # Run the V2 scoring engine: 7 bucket scorers + normalized overall score.
    # overall = Σ(bucket_score × weight) / Σ(weight), so a perfect resume reaches 100
    # regardless of the configured weights' total (see parser_engine/scoring/config.py).
    result = score_resume(raw_text, extracted)
    overall = result.overall_score

    # Save to DB
    db = SessionLocal()

    try:
        upload_row = db.query(models.ResumeUpload).filter_by(id=upload_id).first()
        if not upload_row:
            upload_row = models.ResumeUpload(
                id=upload_id,
                user_id=current_user.id,
                file_name=f"{upload_id}.pdf",
                file_path=str(pdf_path),
                status="parsed"
            )
            db.add(upload_row)

        resume_row = db.query(models.Resume).filter_by(id=upload_id).first()
        if not resume_row:
            resume_row = models.Resume(
                id=upload_id,
                upload_id=upload_id,
                raw_text=raw_text,
                contact_info=json.dumps(extracted.get("contact", {})),
                summary=None,
                education=json.dumps([]),
                skills=json.dumps(extracted.get("skills", [])),
                experience=json.dumps(extracted.get("experience_blocks", [])),
                projects=json.dumps(extracted.get("projects", [])),
                certifications=json.dumps([]),
                achievements=json.dumps([]),
                formatting=json.dumps({}),
                overall_score=overall,
                scoring_version=result.scoring_version,
                score_timestamp=datetime.now(timezone.utc),
                scoring_config_version=result.scoring_version,
            )
            db.add(resume_row)
        else:
            resume_row.raw_text = raw_text
            resume_row.contact_info = json.dumps(extracted.get("contact", {}))
            resume_row.skills = json.dumps(extracted.get("skills", []))
            resume_row.experience = json.dumps(extracted.get("experience_blocks", []))
            resume_row.projects = json.dumps(extracted.get("projects", []))
            resume_row.overall_score = overall
            resume_row.scoring_version = result.scoring_version
            resume_row.score_timestamp = datetime.now(timezone.utc)
            resume_row.scoring_config_version = result.scoring_version

            db.query(models.ResumeBucket).filter_by(resume_id=upload_id).delete()
            db.query(models.ResumeMistake).filter_by(resume_id=upload_id).delete()
        # Save bucket scores + findings (structured evidence/feedback)
        for bucket in result.buckets:
            bucket_id = str(uuid.uuid4())
            bucket_row = models.ResumeBucket(
                id=bucket_id,
                resume_id=upload_id,
                bucket_name=bucket.name,
                score=bucket.raw_score,
                max_score=bucket.max_score,
                weight=bucket.weight,
                weighted_score=bucket.weighted_score,
            )
            db.add(bucket_row)

            for finding in bucket.findings:
                mrow = models.ResumeMistake(
                    id=str(uuid.uuid4()),
                    resume_id=upload_id,
                    category=finding.category,
                    mistake=finding.message,
                    feedback=finding.feedback,
                    section=finding.section,
                    severity=finding.severity.value if finding.severity else None,
                    criterion=finding.criterion,
                    finding_type=finding.type,
                    value=finding.value,
                    expected=finding.expected,
                    impact=finding.impact,
                )
                db.add(mrow)

        upload_row.status = "processed"

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"DB Error: {e}")

    finally:
        db.close()

    return {
        "resume_id": upload_id,
        "overall_score": overall,
        "scoring_version": result.scoring_version,
        "weight_total": result.weight_total,
        "buckets": [
            {
                "name": bucket.name,
                "score": bucket.raw_score,
                "weight": bucket.weight,
                "weighted_score": bucket.weighted_score,
            }
            for bucket in result.buckets
        ]
    }

# ---------------------------------------------------
# Get Full Resume Report
# ---------------------------------------------------
@app.get("/resumes/{resume_id}")
def get_resume_report(
    resume_id: str = FastAPIPath(..., description="UUID of resume"),
    current_user: models.User = Depends(get_current_user),
):
    db = SessionLocal()

    try:
        # ----------------------------
        # Fetch resume
        # ----------------------------
        resume = (
            db.query(models.Resume)
            .filter(models.Resume.id == resume_id)
            .first()
        )

        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        if current_user.role == Role.STUDENT:
            upload_row = db.query(models.ResumeUpload).filter_by(id=resume.upload_id).first()
            if not upload_row or upload_row.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="You do not have permission to perform this action.")

        # ----------------------------
        # Fetch buckets
        # ----------------------------
        bucket_rows = (
            db.query(models.ResumeBucket)
            .filter(models.ResumeBucket.resume_id == resume_id)
            .all()
        )

        buckets = [
            {
                "name": b.bucket_name,
                "score": b.score,
                "weight": b.weight,
                "max_score": b.max_score,
                "weighted_score": b.weighted_score,
            }
            for b in bucket_rows
        ]
        weight_total = sum(b.weight for b in bucket_rows) if bucket_rows else None

        # ----------------------------
        # Fetch mistakes
        # ----------------------------
        mistake_rows = (
            db.query(models.ResumeMistake)
            .filter(models.ResumeMistake.resume_id == resume_id)
            .all()
        )

        mistakes = [
            {
                "category": m.category,
                "mistake": m.mistake,
                "feedback": m.feedback,
                "section": m.section,
                "severity": m.severity,
                "criterion": m.criterion,
                "type": m.finding_type,
                "value": m.value,
                "expected": m.expected,
                "impact": m.impact,
            }
            for m in mistake_rows
        ]

        # ----------------------------
        # Generate deep report (NEW)
        # ----------------------------
        report_summary = generate_resume_report(buckets, mistakes)

        # ----------------------------
        # Build response
        # ----------------------------
        return {
            "resume_id": resume_id,
            "overall_score": resume.overall_score,
            "scoring_version": resume.scoring_version,
            "weight_total": weight_total,
            "contact_info": json.loads(resume.contact_info or "{}"),
            "skills": json.loads(resume.skills or "[]"),
            "experience": json.loads(resume.experience or "[]"),
            "projects": json.loads(resume.projects or "[]"),
            "education": json.loads(resume.education or "[]"),
            "certifications": json.loads(resume.certifications or "[]"),
            "achievements": json.loads(resume.achievements or "[]"),
            "raw_text_length": len(resume.raw_text) if resume.raw_text else 0,
            "buckets": buckets,
            "mistakes": mistakes,
            "report": report_summary,  # ⭐ this powers the UI
        }

    except HTTPException:
        # Preserve FastAPI errors (404 etc.)
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {e}"
        )

    finally:
        db.close()

@app.get("/resumes")
def list_resumes(
    min_score: int = 0,
    max_score: int = 100,
    missing_linkedin: bool = False,
    missing_github: bool = False,
    no_projects: bool = False,
    sort_by: str = "score_desc",  # options: score_desc, score_asc, latest, oldest
    current_user: models.User = Depends(get_current_user),
):
    db = SessionLocal()

    try:
        q = db.query(models.Resume)
        q = _scope_to_own_resumes(q, current_user)

        # Score filtering
        q = q.filter(models.Resume.overall_score >= min_score)
        q = q.filter(models.Resume.overall_score <= max_score)

        # Helper: load JSON fields
        def parse_json(val, fallback):
            try:
                return json.loads(val) if val else fallback
            except:
                return fallback

        resumes = q.all()
        results = []

        for r in resumes:
            contact = parse_json(r.contact_info, {})
            projects = parse_json(r.projects, [])

            # Filtering logic
            if missing_linkedin and contact.get("linkedin"):
                continue
            if missing_github and contact.get("github"):
                continue
            if no_projects and len(projects) > 0:
                continue

            results.append({
                "resume_id": r.id,
                "overall_score": r.overall_score,
                "contact_info": contact,
                "projects_count": len(projects),
                "created_at": r.created_at.isoformat() if r.created_at else None
            })

        # Sorting logic
        if sort_by == "score_desc":
            results = sorted(results, key=lambda x: x["overall_score"], reverse=True)
        elif sort_by == "score_asc":
            results = sorted(results, key=lambda x: x["overall_score"])
        elif sort_by == "latest":
            results = sorted(results, key=lambda x: x["created_at"] or "", reverse=True)
        elif sort_by == "oldest":
            results = sorted(results, key=lambda x: x["created_at"] or "")

        return {"count": len(results), "resumes": results}

    except Exception as e:
        raise HTTPException(500, f"DB error: {e}")

    finally:
        db.close()

@app.get("/export/json")
def export_json(current_user: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        resumes = _scope_to_own_resumes(db.query(models.Resume), current_user).all()
        rows = build_resume_export_rows(resumes)
        return rows
    finally:
        db.close()


@app.get("/export/csv")
def export_csv(current_user: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        resumes = _scope_to_own_resumes(db.query(models.Resume), current_user).all()
        rows = build_resume_export_rows(resumes)

        if not rows:
            raise HTTPException(404, "No resumes found")

        # Create CSV in-memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

        output.seek(0)

        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=resumes.csv"}
        )
    finally:
        db.close()

@app.get("/export/excel")
def export_excel(current_user: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        resumes = _scope_to_own_resumes(db.query(models.Resume), current_user).all()
        rows = build_resume_export_rows(resumes)

        if not rows:
            raise HTTPException(404, "No resumes found")

        try:
            df = pd.DataFrame(rows)
        except Exception as e:
            raise HTTPException(500, f"DataFrame build error: {e}")

        output = io.BytesIO()

        try:
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Resumes")
        except Exception as e:
            raise HTTPException(500, f"Excel writing error: {e}")

        # IMPORTANT: reset pointer
        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=resumes.xlsx"}
        )

    except Exception as e:
        raise HTTPException(500, f"Export error: {e}")

    finally:
        db.close()
@app.post("/admin/reset-db")
def reset_database(current_user: models.User = Depends(require_role(Role.ADMIN))):
    """
    Safe DB reset for SQLite on Windows:
    Drops and recreates all tables AND cleans upload directory.
    """
    from backend.app.db import engine, SessionLocal

    try:
        # Close all active DB sessions
        db = SessionLocal()
        db.close()

        # Dispose engine connections
        engine.dispose()

        # Drop and recreate resume-data tables only. `users` is deliberately excluded --
        # this reset was wiping every user account (including the admin calling it) before
        # authentication existed to protect it; user accounts are a separate concern from
        # resume data.
        resume_data_tables = [
            models.ResumeMistake.__table__,
            models.ResumeBucket.__table__,
            models.Resume.__table__,
            models.ResumeUpload.__table__,
        ]
        Base.metadata.drop_all(bind=engine, tables=resume_data_tables)
        Base.metadata.create_all(bind=engine, tables=resume_data_tables)

        # Clean upload directory - remove all uploaded PDF files
        files_deleted = 0
        if UPLOAD_DIR.exists():
            for file_path in UPLOAD_DIR.glob("*.pdf"):
                try:
                    file_path.unlink()  # Delete the file
                    files_deleted += 1
                except Exception as e:
                    # Log error but continue cleanup
                    print(f"Warning: Failed to delete {file_path.name}: {e}")

        return {
            "status": "success",
            "message": f"Database reset successfully. {files_deleted} uploaded file(s) deleted."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

#---------------------------------------------------
def build_resume_export_rows(db_rows):
    """
    Convert Resume DB rows into a list of dictionaries for export.
    Merges bucket scores into a flat row.
    """
    rows = []
    for r in db_rows:
        try:
            buckets = {b.bucket_name: b.score for b in r.buckets}
        except:
            buckets = {}

        row = {
            "resume_id": r.id,
            "overall_score": r.overall_score,
            "email": "",
            "phone": "",
            "linkedin": "",
            "github": "",
            "projects_count": 0,
        }

        # contact info
        try:
            contact = json.loads(r.contact_info or "{}")
            row["email"] = ", ".join(contact.get("emails", []))
            row["phone"] = ", ".join(contact.get("phones", []))
            row["linkedin"] = contact.get("linkedin", "")
            row["github"] = contact.get("github", "")
        except:
            pass

        # projects count
        try:
            projects = json.loads(r.projects or "[]")
            row["projects_count"] = len(projects)
        except:
            pass

        # merge buckets
        for k, v in buckets.items():
            row[k] = v

        rows.append(row)

    return rows
