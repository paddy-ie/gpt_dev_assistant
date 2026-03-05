from fastapi import APIRouter

from app.api.routes import assistant, auth, automations, health, runs, telemetry

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(runs.router)
api_router.include_router(automations.router)
api_router.include_router(telemetry.router)
api_router.include_router(assistant.router)
