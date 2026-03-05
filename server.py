from __future__ import annotations

import os
from flask import Flask

from api import create_api_blueprint
from assistant import assistant_bp
from agent import agent_bp
from frontend import frontend_bp
from utils.paths import WORKSPACE_ROOT


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(WORKSPACE_ROOT.parent / "frontend" / "templates"),
        static_folder=str(WORKSPACE_ROOT.parent / "frontend" / "static"),
    )
    app.config.update(
        SECRET_KEY=os.environ.get("IDE_SECRET_KEY", "dev-secret"),
        JSON_SORT_KEYS=False,
        TEMPLATES_AUTO_RELOAD=True,
    )

    app.register_blueprint(frontend_bp)
    app.register_blueprint(create_api_blueprint())
    app.register_blueprint(assistant_bp)
    app.register_blueprint(agent_bp)

    @app.after_request
    def no_cache(response):
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault("X-Workspace-Root", WORKSPACE_ROOT.as_posix())
        return response

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)

