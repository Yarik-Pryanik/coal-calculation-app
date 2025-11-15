import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Получаем URL базы данных из переменных окружения
DATABASE_URL = os.getenv('DATABASE_URL')

# Если DATABASE_URL не установлена, используем SQLite для разработки
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./coal_calculation.db"

# Render использует postgres://, но SQLAlchemy требует postgresql://
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
