from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="MandateCore",
    description="Runtime authority validation for AI-influenced banking decisions.",
    version="0.1.0",
)

app.include_router(router)
