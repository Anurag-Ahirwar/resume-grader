# backend/app/create_db.py
from .db import engine, Base
from . import models

def create_all():
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

if __name__ == "__main__":
    create_all()
