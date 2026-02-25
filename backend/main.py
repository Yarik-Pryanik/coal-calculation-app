from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import engine, Base, GITHUB_TOKEN, GITHUB_REPO
import models
from routers.coal import router as coal_router
from routers.boiler import router as boiler_router
from routers.calculations import router as calculations_router

# Создаем таблицы в базе данных при запуске
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
except Exception as e:
    print(f"❌ Database error: {e}")

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

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)



