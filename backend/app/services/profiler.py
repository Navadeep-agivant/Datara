from typing import List
import pandas as pd
import numpy as np
from app.models.profile import ColumnProfile, NumericStats, CategoricalStats, DatetimeStats, TopValue, InferredType

def infer_column_type(series: pd.Series, col_name: str) -> InferredType:
    col_lower = col_name.lower()
    if "id" in col_lower or "key" in col_lower or "code" in col_lower:
        return "identifier"
    
    # Check datetime
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if series.dtype == "object":
        sample = series.dropna().astype(str).head(50)
        if len(sample) > 0 and ("date" in col_lower or "time" in col_lower):
            try:
                pd.to_datetime(sample, errors='raise')
                return "datetime"
            except Exception:
                pass

    if pd.api.types.is_numeric_dtype(series):
        if series.nunique() <= 10 and not ("amount" in col_lower or "price" in col_lower or "qty" in col_lower):
            return "categorical"
        return "numeric"

    # Low cardinality string
    if series.nunique() <= 50 or (len(series) > 0 and series.nunique() / len(series) < 0.2):
        return "categorical"

    return "text"

def profile_dataframe(df: pd.DataFrame) -> List[ColumnProfile]:
    profiles = []
    total_rows = len(df)

    for col in df.columns:
        series = df[col]
        null_count = int(series.isna().sum())
        null_pct = float(round((null_count / max(total_rows, 1)) * 100, 2))
        unique_count = int(series.nunique(dropna=True))
        
        # Example values
        non_null_samples = series.dropna().astype(str).unique()[:5].tolist()

        inferred_type = infer_column_type(series, col)
        stats = None

        if inferred_type == "numeric":
            clean_num = pd.to_numeric(series, errors='coerce').dropna()
            if not clean_num.empty:
                std_val = float(clean_num.std()) if len(clean_num) > 1 else 0.0
                stats = NumericStats(
                    min=float(clean_num.min()),
                    max=float(clean_num.max()),
                    mean=float(round(clean_num.mean(), 2)),
                    median=float(round(clean_num.median(), 2)),
                    std=float(round(0.0 if np.isnan(std_val) else std_val, 2)),
                    is_constant=bool(clean_num.nunique() <= 1)
                )
        elif inferred_type in ("categorical", "identifier", "text"):
            vc = series.astype(str).value_counts().head(10)
            top_vals = [TopValue(value=str(idx), count=int(cnt)) for idx, cnt in vc.items()]
            stats = CategoricalStats(top_values=top_vals)

        profiles.append(ColumnProfile(
            column_name=col,
            inferred_type=inferred_type,
            total_rows=total_rows,
            null_count=null_count,
            null_pct=null_pct,
            unique_count=unique_count,
            example_values=non_null_samples,
            stats=stats
        ))

    return profiles
