# backend/app/create_admin.py
"""Bootstrap the first admin user. Run from the repo root:

    python -m backend.app.create_admin

Refuses to run if an admin already exists unless --force is passed, so it's safe to
re-run by accident. Never accepts a password as a CLI argument (would leak into shell
history / process list) -- always prompts via getpass (hidden input).
"""
import argparse
import getpass
import sys
import uuid

from backend.app.auth import Role, hash_password
from backend.app.db import Base, SessionLocal, engine, ensure_columns
from backend.app import models


def main():
    parser = argparse.ArgumentParser(description="Create the first Resume Grader admin user.")
    parser.add_argument("--force", action="store_true", help="Create another admin even if one already exists.")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    ensure_columns()

    db = SessionLocal()
    try:
        existing_admin = db.query(models.User).filter_by(role=Role.ADMIN).first()
        if existing_admin and not args.force:
            print(f"An admin already exists ({existing_admin.email}). Re-run with --force to add another.")
            sys.exit(1)

        email = input("Admin email: ").strip().lower()
        if not email or "@" not in email:
            print("A valid email is required.")
            sys.exit(1)

        if db.query(models.User).filter_by(email=email).first():
            print(f"A user with email {email} already exists.")
            sys.exit(1)

        name = input("Admin display name: ").strip() or email

        password = getpass.getpass("Admin password: ")
        confirm = getpass.getpass("Confirm password: ")
        if not password or len(password) < 8:
            print("Password must be at least 8 characters.")
            sys.exit(1)
        if password != confirm:
            print("Passwords do not match.")
            sys.exit(1)

        admin = models.User(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=Role.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"Admin user created: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
