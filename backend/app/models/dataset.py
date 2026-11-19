from __future__ import annotations
from pydantic import BaseModel, Field, UUID4

class UploadResponse(BaseModel):
    session_id: UUID4
    filename: str
    row_count: int = Field(ge=1, le=10_000)
    column_count: int = Field(ge=1)
    encoding: str
    parse_warnings: list[str] = []

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict = {}
