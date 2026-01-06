import logging
from sqlmodel import SQLModel

from app.db.session import engine
# Import models to register them with SQLModel.metadata
from app.db import models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    logger.info("Creating initial database tables...")
    SQLModel.metadata.create_all(engine)
    logger.info("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
