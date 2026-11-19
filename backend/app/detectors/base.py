from abc import ABC, abstractmethod
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from app.models.finding import Finding

def clean_record_for_json(record: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = {}
    for k, v in record.items():
        if pd.isna(v) or v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
            cleaned[k] = None
        else:
            cleaned[k] = v
    return cleaned

def clean_records_for_json(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [clean_record_for_json(r) for r in records]

class BaseDetector(ABC):
    @abstractmethod
    def detect(self, df: pd.DataFrame) -> List[Finding]:
        """Run anomaly detection algorithm on the provided DataFrame and return structured findings."""
        pass
