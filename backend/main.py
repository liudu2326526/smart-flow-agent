import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import chat, conversations, documents

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(chat.router, prefix=f"{settings.API_V1_STR}", tags=["chat"])
app.include_router(conversations.router, prefix=f"{settings.API_V1_STR}", tags=["conversations"])
app.include_router(documents.router, prefix=f"{settings.API_V1_STR}", tags=["documents"])

@app.get("/")
def root():
    return {
        "code": 200,
        "message": "Welcome to SmartFlow Agent Hub API",
        "data": {
            "docs_url": "/docs",
            "redoc_url": "/redoc"
        }
    }

@app.get("/health")
def health_check():
    return {
        "code": 200,
        "message": "success",
        "data": {"status": "ok"}
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
