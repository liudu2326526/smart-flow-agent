from sqlmodel import create_engine, Session
from app.core.config import settings

# check_same_thread=False is needed for SQLite
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})

def get_session():
    with Session(engine) as session:
        yield session
