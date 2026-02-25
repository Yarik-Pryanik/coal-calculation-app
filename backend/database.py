import os
import base64
import json
import tempfile
import time
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import requests

# GitHub настройки
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO = os.environ.get('GITHUB_REPO')  # "username/repo"
GITHUB_PATH = "database/coal_calculation.db"  # путь в репозитории

# Временная директория для работы
TEMP_DIR = Path(tempfile.gettempdir()) / "coal_api"
TEMP_DIR.mkdir(exist_ok=True)
DB_PATH = TEMP_DIR / "coal_calculation.db"

def upload_to_github():
    """Загрузить на GitHub"""
    try:
        if not GITHUB_TOKEN or not GITHUB_REPO or not DB_PATH.exists():
            return False
        
        with open(DB_PATH, 'rb') as f:
            content = base64.b64encode(f.read()).decode()
        
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        
        get_response = requests.get(url, headers=headers)
        
        data = {
            "message": f"Auto-backup {datetime.now().isoformat()}",
            "content": content
        }
        
        if get_response.status_code == 200:
            data["sha"] = get_response.json()['sha']
        
        response = requests.put(url, json=data, headers=headers)
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"GitHub error: {e}")
        return False

# Фоновое сохранение каждые 5 минут
def auto_save_loop():
    while True:
        time.sleep(300)  # 5 минут
        try:
            upload_to_github()
            print(f"💾 Auto-saved at {datetime.now().strftime('%H:%M:%S')}")
        except:
            pass

# Запускаем фоновый поток
threading.Thread(target=auto_save_loop, daemon=True).start()

# Скачиваем при старте
try:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.json()['content']
        with open(DB_PATH, 'wb') as f:
            f.write(base64.b64decode(content))
        print("✅ Database loaded from GitHub")
except:
    print("⚠️ New database")

# SQLAlchemy
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
