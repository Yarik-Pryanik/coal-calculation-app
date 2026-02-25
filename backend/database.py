import os
import shutil
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Определяем окружение
IS_RENDER = os.environ.get('RENDER', False)

# Директория для данных
if IS_RENDER:
    DATA_DIR = Path('/tmp/data')
else:
    DATA_DIR = Path("data")

DATA_DIR.mkdir(exist_ok=True, parents=True)

DB_PATH = DATA_DIR / "coal_calculation.db"
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True, parents=True)

# SQLite движок
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_backup():
    """Создание бэкапа базы данных"""
    try:
        if not DB_PATH.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"backup_{timestamp}.db"
        
        shutil.copy2(DB_PATH, backup_path)
        
        # Оставляем последние 3 бэкапов
        backups = sorted(BACKUP_DIR.glob("backup_*.db"))
        for old_backup in backups[:-3]:
            old_backup.unlink()
        
        return str(backup_path)
    except Exception as e:
        print(f"Backup error: {e}")
        return None

def list_backups():
    """Список бэкапов"""
    backups = sorted(BACKUP_DIR.glob("backup_*.db"), reverse=True)
    return [{
        "name": b.name,
        "size_kb": round(b.stat().st_size / 1024, 2),
        "created_at": datetime.fromtimestamp(b.stat().st_mtime).isoformat()
    } for b in backups]

