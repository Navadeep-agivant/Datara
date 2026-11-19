import io
from typing import Tuple, List
import pandas as pd

MAX_SUPPORTED_ROWS = 10_000

def ingest_csv(content: bytes, filename: str) -> Tuple[pd.DataFrame, str, List[str]]:
    warnings: List[str] = []
    if not content:
        raise ValueError("The uploaded file contains no data rows.")

    detected_encoding = "utf-8"
    if content.startswith(b"\xef\xbb\xbf"):
        detected_encoding = "utf-8-sig"

    try:
        buffer = io.BytesIO(content)
        # Attempt to read CSV with python engine for delimiter sniffing fallback
        try:
            df = pd.read_csv(buffer, encoding=detected_encoding, sep=None, engine='python')
        except Exception:
            buffer.seek(0)
            df = pd.read_csv(buffer, encoding=detected_encoding)
    except Exception as e:
        raise ValueError(f"Failed to parse CSV file: {str(e)}")

    if df.empty:
        raise ValueError("The uploaded file contains no data rows.")

    if len(df) > MAX_SUPPORTED_ROWS:
        raise ValueError(f"Maximum supported rows: {MAX_SUPPORTED_ROWS}. Uploaded: {len(df)}")

    # Clean header whitespaces
    df.columns = [str(c).strip() for c in df.columns]
    if df.columns.duplicated().any():
        warnings.append("Duplicate column headers were detected and renamed.")
        # Make duplicate columns unique
        s = pd.Series(df.columns)
        duplicates = s.duplicated()
        s_counts = s.groupby(s).cumcount().astype(str)
        df.columns = s.where(~duplicates, s + "_" + s_counts)

    return df, detected_encoding, warnings
