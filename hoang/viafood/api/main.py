from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import health, init, chat, upload, stats, reset
from fastapi.responses import JSONResponse

app = FastAPI(title="Vietnamese Food RAG API")

@app.get("/")
def root():
    return JSONResponse(content={"message": "👋 Đây là API tư vấn món ăn Việt Nam"})
# CORS cho mobile/web app

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(init.router)
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(stats.router)
app.include_router(reset.router)
