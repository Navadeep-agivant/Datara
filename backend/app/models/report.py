from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel
from .cleaning import CleaningOperation

class TransformationLog(BaseModel):
    session_id: str
    entries: list[CleaningOperation] = []
    exported_at: datetime
