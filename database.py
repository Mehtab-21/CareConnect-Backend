from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# This matches the user/pass you created in Phase 1
SQLALCHEMY_DATABASE_URL = "postgresql://care_admin:care123@localhost/careconnect"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    # The connect_args is only needed for SQLite. Remove it if using PostgreSQL.
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get a database session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()