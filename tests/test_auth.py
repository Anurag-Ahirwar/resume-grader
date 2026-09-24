"""Unit tests for backend/app/auth.py: password hashing and JWT issuing/verification.
Pure unit tests, no DB or running server needed.
"""
import time

import jwt
import pytest

from backend.app.auth import (
    ALGORITHM,
    SESSION_SECRET,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class _FakeUser:
    def __init__(self, id="u1", role="recruiter"):
        self.id = id
        self.role = role


# ---------------------------------------------------
# Password hashing
# ---------------------------------------------------

def test_password_is_hashed_not_stored_plaintext():
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")  # bcrypt format


def test_correct_password_verifies():
    hashed = hash_password("s3cret-pw!")
    assert verify_password("s3cret-pw!", hashed) is True


def test_incorrect_password_fails():
    hashed = hash_password("s3cret-pw!")
    assert verify_password("wrong-password", hashed) is False


def test_verify_password_handles_missing_hash_gracefully():
    assert verify_password("anything", "") is False
    assert verify_password("anything", None) is False


def test_two_hashes_of_same_password_differ():
    # bcrypt salts each hash, so identical passwords must not produce identical hashes.
    h1 = hash_password("same-password")
    h2 = hash_password("same-password")
    assert h1 != h2
    assert verify_password("same-password", h1)
    assert verify_password("same-password", h2)


# ---------------------------------------------------
# JWT
# ---------------------------------------------------

def test_create_and_decode_token_roundtrip():
    user = _FakeUser(id="abc-123", role="admin")
    token = create_access_token(user)
    payload = decode_access_token(token)
    assert payload["sub"] == "abc-123"
    assert payload["role"] == "admin"


def test_tampered_token_rejected():
    user = _FakeUser()
    token = create_access_token(user)
    tampered = token[:-4] + ("AAAA" if token[-4:] != "AAAA" else "BBBB")
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(tampered)


def test_expired_token_rejected():
    user = _FakeUser()
    expired_payload = {
        "sub": user.id,
        "role": user.role,
        "iat": int(time.time()) - 120,
        "exp": int(time.time()) - 60,  # expired 1 minute ago
    }
    expired_token = jwt.encode(expired_payload, SESSION_SECRET, algorithm=ALGORITHM)
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired_token)


def test_token_signed_with_wrong_secret_rejected():
    forged = jwt.encode({"sub": "u1", "role": "admin"}, "not-the-real-secret", algorithm=ALGORITHM)
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(forged)
