from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def create_sqlite_engine(sqlite_url: str | None = None) -> Engine:
    settings = get_settings()
    settings.ensure_runtime_dirs()
    url = sqlite_url or settings.sqlite_url
    return create_engine(url, connect_args={"check_same_thread": False})


engine = create_sqlite_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
