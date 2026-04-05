from __future__ import annotations
"""Configuración de SQLAlchemy + SQLite."""
from pathlib import Path
import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

APP_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
RUNTIME_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else APP_DIR
DATA_DIR = Path(os.environ.get("CATALOGOS_DATA_DIR", str(RUNTIME_DIR / "data")))
UPLOADS_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "catalogs.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Importar aquí para registrar los modelos antes de create_all.
    from models import Catalog, Product  # noqa: F401
    Base.metadata.create_all(engine)
