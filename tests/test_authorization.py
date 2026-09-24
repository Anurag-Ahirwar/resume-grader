"""Endpoint-level authentication & authorization tests, against the real FastAPI app
wired to a throwaway SQLite file (see conftest.py -- RESUME_GRADER_DB_URL is redirected
there before this module is even imported).

Covers the authorization matrix from the V3 execution plan: every role x every
protected endpoint, plus /admin/reset-db specifically for all 4 actor types.
"""
import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.app.auth import hash_password
from backend.app.db import Base, SessionLocal, engine
from backend.app import models
from backend.app.main import app, UPLOAD_DIR

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def _fresh_schema():
    Base.metadata.create_all(bind=engine)
    yield


def _make_user(db, email, password, role, is_active=True):
    """Returns a plain SimpleNamespace snapshot (id, email), not the live ORM object --
    the session this creates the user in is closed before the caller can use it, and
    SQLAlchemy expires ORM attributes on commit (DetachedInstanceError on next access)."""
    user_id = str(uuid.uuid4())
    db.add(models.User(
        id=user_id,
        name=email.split("@")[0],
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
    ))
    db.commit()
    return SimpleNamespace(id=user_id, email=email, role=role)


@pytest.fixture(scope="module")
def users():
    db = SessionLocal()
    try:
        return {
            "admin": _make_user(db, "admin@test.local", "adminpass123", "admin"),
            "recruiter": _make_user(db, "recruiter@test.local", "recruiterpass123", "recruiter"),
            "student_a": _make_user(db, "student.a@test.local", "studentpass123", "student"),
            "student_b": _make_user(db, "student.b@test.local", "studentpass123", "student"),
            "inactive": _make_user(db, "inactive@test.local", "inactivepass123", "recruiter", is_active=False),
        }
    finally:
        db.close()


def _login(email, password):
    response = client.post("/auth/login", data={"username": email, "password": password})
    return response


@pytest.fixture(scope="module")
def tokens(users):
    return {
        role: _login(user.email, {
            "admin": "adminpass123", "recruiter": "recruiterpass123",
            "student_a": "studentpass123", "student_b": "studentpass123",
        }[role]).json()["access_token"]
        for role, user in users.items() if role != "inactive"
    }


def _auth(role, tokens):
    return {"Authorization": f"Bearer {tokens[role]}"}


# ---------------------------------------------------
# Login
# ---------------------------------------------------

def test_login_valid_credentials_succeeds(users):
    response = _login("admin@test.local", "adminpass123")
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "admin"
    assert "access_token" in body
    assert "password" not in body and "password_hash" not in body


def test_login_invalid_password_fails(users):
    response = _login("admin@test.local", "wrong-password")
    assert response.status_code == 401
    assert "traceback" not in response.text.lower()


def test_login_unknown_email_fails():
    response = _login("nobody@test.local", "whatever123")
    assert response.status_code == 401
    # Same error for unknown-user vs wrong-password -- no account enumeration.
    assert response.json()["detail"] == "Invalid username or password."


def test_login_missing_credentials_fails():
    response = client.post("/auth/login", data={"username": "admin@test.local"})
    assert response.status_code == 422


def test_inactive_user_cannot_authenticate(users):
    response = _login("inactive@test.local", "inactivepass123")
    assert response.status_code == 401


# ---------------------------------------------------
# Authentication (generic)
# ---------------------------------------------------

def test_health_is_public():
    assert client.get("/health").status_code == 200


def test_auth_me_requires_authentication():
    assert client.get("/auth/me").status_code == 401


def test_auth_me_succeeds_when_authenticated(tokens):
    response = client.get("/auth/me", headers=_auth("admin", tokens))
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_unauthenticated_request_to_protected_endpoint_rejected():
    assert client.get("/resumes").status_code == 401


def test_authenticated_request_succeeds(tokens):
    assert client.get("/resumes", headers=_auth("recruiter", tokens)).status_code == 200


def test_invalid_token_rejected():
    response = client.get("/resumes", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


# ---------------------------------------------------
# Authorization matrix
# ---------------------------------------------------

def test_upload_requires_authentication():
    files = [("files", ("resume.pdf", b"%PDF-1.4 fake", "application/pdf"))]
    assert client.post("/resumes/upload", files=files).status_code == 401


@pytest.mark.parametrize("role", ["student_a", "recruiter", "admin"])
def test_upload_allowed_for_every_authenticated_role(role, tokens):
    files = [("files", ("resume.pdf", b"%PDF-1.4 fake", "application/pdf"))]
    response = client.post("/resumes/upload", files=files, headers=_auth(role, tokens))
    assert response.status_code == 200
    assert len(response.json()["upload_ids"]) == 1


def test_upload_csv_forbidden_for_student(tokens):
    files = {"file": ("resumes.csv", b"resume_link\n", "text/csv")}
    response = client.post("/resumes/upload-csv", files=files, headers=_auth("student_a", tokens))
    assert response.status_code == 403


@pytest.mark.parametrize("role", ["recruiter", "admin"])
def test_upload_csv_allowed_for_recruiter_and_admin(role, tokens):
    files = {"file": ("resumes.csv", b"resume_link\n", "text/csv")}
    response = client.post("/resumes/upload-csv", files=files, headers=_auth(role, tokens))
    assert response.status_code == 200  # empty CSV is valid, just processes 0 rows


@pytest.mark.parametrize("role", ["student_a", "recruiter"])
def test_debug_endpoints_forbidden_for_non_admin(role, tokens):
    response = client.post("/debug/parse-pdf", json={"upload_id": "does-not-matter"}, headers=_auth(role, tokens))
    assert response.status_code == 403


def test_debug_endpoint_reaches_business_logic_for_admin(tokens):
    # 404 (not 401/403) proves the auth layer let an admin through to the real handler.
    response = client.post("/debug/parse-pdf", json={"upload_id": "does-not-exist"}, headers=_auth("admin", tokens))
    assert response.status_code == 404


@pytest.mark.parametrize("role", ["student_a", "recruiter", "admin"])
def test_admin_reset_db_rejects_non_admin_and_unauthenticated(role, tokens):
    if role == "admin":
        return  # covered separately below (destructive, run once)
    response = client.post("/admin/reset-db", headers=_auth(role, tokens))
    assert response.status_code == 403


def test_admin_reset_db_rejects_unauthenticated():
    assert client.post("/admin/reset-db").status_code == 401


def test_admin_reset_db_allowed_for_admin(tokens, users):
    response = client.post("/admin/reset-db", headers=_auth("admin", tokens))
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    # Users must survive a data reset -- otherwise the admin who just called this would
    # be logged out of their own account the moment they use the feature.
    db = SessionLocal()
    try:
        assert db.query(models.User).filter_by(email="admin@test.local").first() is not None
    finally:
        db.close()


# ---------------------------------------------------
# Student ownership scoping
# ---------------------------------------------------

def _seed_owned_resume(owner_user_id):
    """Creates a minimal ResumeUpload + Resume pair owned by the given user, and a
    matching dummy PDF on disk (process_resume checks file existence before ownership)."""
    upload_id = str(uuid.uuid4())
    pdf_path = UPLOAD_DIR / f"{upload_id}.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    db = SessionLocal()
    try:
        db.add(models.ResumeUpload(
            id=upload_id, user_id=owner_user_id, file_name=f"{upload_id}.pdf",
            file_path=str(pdf_path), status="uploaded",
        ))
        db.add(models.Resume(
            id=upload_id, upload_id=upload_id, raw_text="dummy",
            overall_score=50.0, scoring_version="2.0",
        ))
        db.commit()
    finally:
        db.close()
    return upload_id


@pytest.fixture
def owned_resume(users):
    upload_id = _seed_owned_resume(users["student_a"].id)
    yield upload_id
    (UPLOAD_DIR / f"{upload_id}.pdf").unlink(missing_ok=True)


def test_student_can_view_own_resume(owned_resume, tokens):
    response = client.get(f"/resumes/{owned_resume}", headers=_auth("student_a", tokens))
    assert response.status_code == 200


def test_student_cannot_view_another_students_resume(owned_resume, tokens):
    response = client.get(f"/resumes/{owned_resume}", headers=_auth("student_b", tokens))
    assert response.status_code == 403


@pytest.mark.parametrize("role", ["recruiter", "admin"])
def test_recruiter_and_admin_can_view_any_resume(owned_resume, role, tokens):
    response = client.get(f"/resumes/{owned_resume}", headers=_auth(role, tokens))
    assert response.status_code == 200


def test_student_resume_list_is_scoped_to_own(owned_resume, tokens):
    mine = client.get("/resumes", headers=_auth("student_a", tokens)).json()
    others = client.get("/resumes", headers=_auth("student_b", tokens)).json()

    mine_ids = {r["resume_id"] for r in mine["resumes"]}
    others_ids = {r["resume_id"] for r in others["resumes"]}

    assert owned_resume in mine_ids
    assert owned_resume not in others_ids


def test_student_cannot_process_another_students_upload(owned_resume, tokens):
    response = client.post(f"/resumes/process/{owned_resume}", headers=_auth("student_b", tokens))
    assert response.status_code == 403
