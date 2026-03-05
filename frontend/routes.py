from __future__ import annotations

from flask import Blueprint, render_template

frontend_bp = Blueprint(
    "frontend",
    __name__,
    template_folder="templates",
    static_folder="static",
)


@frontend_bp.get("/")
@frontend_bp.get("/ide")
def home():
    return render_template("ide.html")


@frontend_bp.get("/health")
def healthcheck():
    return {"ok": True}

