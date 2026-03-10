from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os

from .ai import generate_roblox_script
from .schemas import GenerateScriptRequest, GenerateScriptResponse


app = FastAPI(
    title="Vibe Coding Prototype API",
    description=(
        "Turns natural-language prompts into Roblox Lua scripts. "
        "This is a prototype matching the AI Engineer role description."
    ),
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


MONGODB_URI = os.getenv("DATABASE_URL")
mongo_client: AsyncIOMotorClient | None = None


@app.on_event("startup")
async def startup_db() -> None:
    global mongo_client
    if MONGODB_URI:
        mongo_client = AsyncIOMotorClient(MONGODB_URI)


@app.on_event("shutdown")
async def shutdown_db() -> None:
    global mongo_client
    if mongo_client:
        mongo_client.close()
        mongo_client = None


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/db-health")
async def db_health() -> dict:
    if not mongo_client:
        return {"ok": False, "error": "No MongoDB client configured (DATABASE_URL missing?)"}
    try:
        await mongo_client.admin.command("ping")
        return {"ok": True}
    except Exception as exc:  # pragma: no cover - diagnostics only
        return {"ok": False, "error": str(exc)}


@app.post("/generate-script", response_model=GenerateScriptResponse)
async def generate_script_endpoint(payload: GenerateScriptRequest) -> GenerateScriptResponse:
    try:
        script = await generate_roblox_script(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - safety net
        raise HTTPException(
            status_code=502,
            detail=f"Upstream AI provider error: {exc!r}",
        ) from exc

    return GenerateScriptResponse(script=script)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

