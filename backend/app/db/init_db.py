from sqlalchemy import Engine

from app.db.models import Base
from app.db.session import engine


def create_db_and_tables(target_engine: Engine | None = None) -> None:
    Base.metadata.create_all(bind=target_engine or engine)
