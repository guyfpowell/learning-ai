from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from routers import generate, coaching
from middleware.auth import APIKeyMiddleware

app = FastAPI(title="Learning AI Service")
app.add_middleware(APIKeyMiddleware)
app.include_router(generate.router, prefix="/generate")
app.include_router(coaching.router, prefix="/coaching")


@app.get("/health")
async def health():
    return {"status": "ok"}
