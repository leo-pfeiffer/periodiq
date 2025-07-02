from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import ROOT_DIR

engine = create_engine(
    f"sqlite:///{ROOT_DIR}/periodiq.db",
    echo=False,
    connect_args={"check_same_thread": False}
)

# Make sure foreign-key enforcement is on (SQLite only)
with engine.connect() as conn:
    conn.exec_driver_sql("PRAGMA foreign_keys = ON")

SessionLocal: sessionmaker = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)
