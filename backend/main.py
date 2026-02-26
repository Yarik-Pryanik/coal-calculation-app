from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import engine, Base, GITHUB_TOKEN, GITHUB_REPO, save_to_github
import models
from routers.coal import router as coal_router
from routers.boiler import router as boiler_router
from routers.calculations import router as calculations_router
import atexit
import os

try:
    # Проверяем существование таблиц быстрым запросом
    with engine.connect() as conn:
        conn.execute("SELECT 1 FROM coal_data LIMIT 1")
    print("✅ Tables already exist")
except:
    # Создаем только если нет
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created")

app = FastAPI(
    title="Coal Calculation API",
    description="API для расчета параметров работы котлов на основе данных об угле",
    version="1.0.0"
)

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(coal_router)
app.include_router(boiler_router)
app.include_router(calculations_router)

# Отдаем фронтенд для корневого пути
@app.get("/")
def serve_frontend():
    return FileResponse('../frontend/index.html')

# Health check
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running", "github_configured": bool(GITHUB_TOKEN and GITHUB_REPO)}

def shutdown_handler():
    print("\n🛑 Shutting down, saving to GitHub...")
    save_to_github()

atexit.register(shutdown_handler)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)






