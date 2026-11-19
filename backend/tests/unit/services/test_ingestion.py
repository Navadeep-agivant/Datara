import pytest
import io
import pandas as pd
from app.services.ingestion import ingest_csv

def test_ingest_valid_csv():
    csv_bytes = b"col1,col2\n1,a\n2,b\n"
    df, encoding, warnings = ingest_csv(csv_bytes, "test.csv")
    assert len(df) == 2
    assert list(df.columns) == ["col1", "col2"]
    assert encoding in ("utf-8", "utf-8-sig")

def test_ingest_empty_csv_raises_error():
    with pytest.raises(ValueError, match="no data rows"):
        ingest_csv(b"", "empty.csv")

def test_ingest_exceeds_row_limit():
    rows = "\n".join([f"{i}" for i in range(10005)])
    csv_bytes = f"id\n{rows}".encode("utf-8")
    with pytest.raises(ValueError, match="Maximum supported rows"):
        ingest_csv(csv_bytes, "large.csv")

def test_ingest_utf8_bom():
    csv_bytes = b"\xef\xbb\xbfname,age\nAlice,30\n"
    df, encoding, _ = ingest_csv(csv_bytes, "bom.csv")
    assert df.columns[0] == "name"
