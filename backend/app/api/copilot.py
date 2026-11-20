"""Endpoint de consulta aislado, con identidad validada y cuota por usuario."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from backend.app.api.capture import current_user
from backend.app.services.copilot import ChatMessage, answer_copilot

router = APIRouter(prefix="/copiloto", tags=["Copiloto inteligente"])
WINDOW_SECONDS = 60
MAX_PER_MINUTE = 8
MAX_PER_DAY = 80
# Límite por instancia: adecuado para despliegue de un único proceso;
# un escalamiento horizontal exigirá un almacén centralizado.
_usage: dict[str, deque[float]] = defaultdict(deque)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1500)
    history: list[ChatMessage] = Field(default_factory=list, max_length=12)


def check_quota(user_id: str) -> None:
    now = time.monotonic()
    events = _usage[user_id]
    while events and events[0] < now - 86400:
        events.popleft()
    if len(events) >= MAX_PER_DAY or sum(t >= now - WINDOW_SECONDS for t in events) >= MAX_PER_MINUTE:
        raise HTTPException(429, "Se alcanzó el límite de consultas. Intenta más tarde.")
    events.append(now)
    # Limpieza oportunista para evitar acumulación indefinida de claves.
    if len(_usage) > 2000:
        for uid in list(_usage):
            if not _usage[uid] or _usage[uid][-1] < now - 86400:
                _usage.pop(uid, None)


@router.post("/chat")
async def chat(payload: ChatRequest, session=Depends(current_user)):
    profile, _token = session
    if not payload.message.strip():
        raise HTTPException(422, "Escribe una pregunta.")
    check_quota(profile["id"])
    return await answer_copilot(payload.message.strip(), payload.history)
