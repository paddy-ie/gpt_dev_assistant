from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from assistant import history as assistant_history
from assistant.service import ask_assistant

router = APIRouter(prefix="/assistant", tags=["assistant"])


class AssistantFile(BaseModel):
    path: str
    content: str


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    project: str | None = None
    files: list[AssistantFile] | None = None
    model: str | None = None
    temperature: float | None = Field(default=0.2, ge=0.0, le=2.0)


class ChatResponse(BaseModel):
    ok: bool = True
    message: str
    model: str | None = None
    usage: dict | None = None
    messages: list[dict]


@router.get("/history")
def get_history(project: str | None = None, limit: int | None = None) -> dict:
    if limit is not None and limit < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="limit must be positive")
    messages = assistant_history.load_messages(project, limit)
    return {"ok": True, "messages": messages}


@router.post("/history/clear", status_code=status.HTTP_204_NO_CONTENT)
def clear_history(payload: dict | None = None) -> None:
    project = (payload or {}).get("project")
    assistant_history.clear_history(project)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    messages = assistant_history.load_messages(request.project)
    try:
        result = ask_assistant(
            request.prompt,
            project=request.project,
            files=[file.model_dump() for file in request.files] if request.files else None,
            history=messages,
            model=request.model,
            temperature=request.temperature or 0.2,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    assistant_message = result.get("message", "")
    if assistant_message:
        updated_messages = assistant_history.append_exchange(
            request.project,
            request.prompt.strip(),
            assistant_message,
        )
    else:
        updated_messages = messages

    return ChatResponse(
        ok=True,
        message=assistant_message,
        model=result.get("model"),
        usage=result.get("usage"),
        messages=updated_messages,
    )
