import os
import base64
import json
import threading
import tempfile
import time
import atexit
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

db_changed = False
last_save_time = 0
shutting_down = False

def download_from_github():
    """Загрузить базу с GitHub"""
    try:
        if not GITHUB_TOKEN or not GITHUB_REPO:
            return False
        
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            content = response.json()['content']
            with open(DB_PATH, 'wb') as f:
                f.write(base64.b64decode(content))
            print(f"✅ Database loaded from GitHub")
            return True
        else:
            print("⚠️ No existing database on GitHub")
            return False
    except Exception as e:
        print(f"⚠️ Could not load from GitHub: {e}")
        return False

def upload_to_github():
    """Загрузить базу на GitHub"""
    global db_changed, last_save_time, shutting_down
    
    try:
        if shutting_down:
            print("⚠️ Shutting down, skipping save")
            return False
            
        if not GITHUB_TOKEN or not GITHUB_REPO or not DB_PATH.exists():
            return False
        
        if not force and not db_changed:
            return False
        
        # Читаем файл
        with open(DB_PATH, 'rb') as f:
            content = base64.b64encode(f.read()).decode()
        
        # Отправляем на GitHub
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        
        get_response = requests.get(url, headers=headers)
        
        data = {
            "message": f"Backup {datetime.now().isoformat()}",
            "content": content
        }
        
        if get_response.status_code == 200:
            data["sha"] = get_response.json()['sha']
        
        response = requests.put(url, json=data, headers=headers)
        
        if response.status_code in [200, 201]:
            print(f"✅ Saved to GitHub at {datetime.now().strftime('%H:%M:%S')}")
            db_changed = False
            last_save_time = time.time()
            return True
        else:
            print(f"❌ GitHub upload failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ GitHub error: {e}")
        return False

# Фоновое сохранение каждые 5 минут
def auto_save_loop():
    while not shutting_down:
        time.sleep(300)  # 5 минут
        try:
            upload_to_github()
            print(f"💾 Auto-saved at {datetime.now().strftime('%H:%M:%S')}")
        except:
            pass

# Сохранение при выходе
def shutdown_save():
    global shutting_down
    shutting_down = True
    print("\n🛑 Saving before shutdown...")
    if db_changed:
        upload_to_github(force=True)
    print("✅ Shutdown save complete")

# Загружаем базу при старте
download_from_github()

# Запускаем фоновый поток
threading.Thread(target=auto_save_loop, daemon=True).start()

atexit.register(shutdown_save)

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


