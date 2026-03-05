from __future__ import annotations

from flask import Blueprint

from .files import register_file_routes
from .projects import register_project_routes
from .run import register_run_routes


def create_api_blueprint() -> Blueprint:
    bp = Blueprint("api", __name__, url_prefix="/api")
    register_project_routes(bp)
    register_file_routes(bp)
    register_run_routes(bp)
    return bp

