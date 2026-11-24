from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATABASE_URL, sqlalchemy_url

_url = sqlalchemy_url(DATABASE_URL)
_connect_args = {"check_same_thread": False} if _url.startswith("sqlite") else {}

# pool_pre_ping: בודק שהחיבור למסד הנתונים עדיין חי לפני כל שימוש
engine = create_engine(_url, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
