import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.automations.runner import get_automation_runner
from app.core.config import get_settings
from app.db.session import init_db
from app.orchestrator import get_orchestrator
from app.telemetry import get_telemetry_hub

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    loop = asyncio.get_running_loop()
    telemetry = get_telemetry_hub()
    telemetry.set_loop(loop)
    orchestrator = get_orchestrator()
    automation_runner = get_automation_runner()
    await orchestrator.start()
    await automation_runner.start()
    app.state.orchestrator = orchestrator
    app.state.automation_runner = automation_runner
    app.state.telemetry = telemetry
    try:
        yield
    finally:
        await orchestrator.stop()
        await automation_runner.stop()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)
