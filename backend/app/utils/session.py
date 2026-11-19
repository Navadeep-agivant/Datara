from __future__ import annotations
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
import pandas as pd
from app.models.profile import ColumnProfile
from app.models.finding import Finding
from app.models.score import DatasetQualityScore
from app.models.explanation import Explanation
from app.models.cleaning import CleaningOperation

@dataclass
class SessionState:
    session_id: str
    original_df: pd.DataFrame
    working_df: pd.DataFrame
    filename: str
    encoding: str
    parse_warnings: List[str] = field(default_factory=list)
    column_profiles: List[ColumnProfile] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    quality_score_before: Optional[DatasetQualityScore] = None
    quality_score_after: Optional[DatasetQualityScore] = None
    explanations: Dict[str, Explanation] = field(default_factory=dict)
    cleaning_operations: List[CleaningOperation] = field(default_factory=list)
    applied_cleaning_history: List[CleaningOperation] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class SessionStore:
    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}
        self._lock = threading.Lock()

    def create_session(self, session_id: str, df: pd.DataFrame, filename: str, encoding: str, warnings: List[str]) -> SessionState:
        with self._lock:
            # Preserve original immutable dataframe and create a dedicated working copy
            state = SessionState(
                session_id=session_id,
                original_df=df.copy(deep=True),
                working_df=df.copy(deep=True),
                filename=filename,
                encoding=encoding,
                parse_warnings=warnings
            )
            self._sessions[session_id] = state
            return state

    def get_session(self, session_id: str) -> Optional[SessionState]:
        with self._lock:
            return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

# Global singleton in-process session store
session_store = SessionStore()
