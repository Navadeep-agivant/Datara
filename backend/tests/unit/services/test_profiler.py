import pytest
import pandas as pd
from app.services.profiler import profile_dataframe

def test_profile_dataframe():
    df = pd.DataFrame({
        "order_id": ["ORD-1", "ORD-2", "ORD-3"],
        "amount": [10.5, 20.0, None],
        "category": ["A", "B", "A"]
    })
    profiles = profile_dataframe(df)
    assert len(profiles) == 3

    amount_profile = next(p for p in profiles if p.column_name == "amount")
    assert amount_profile.inferred_type == "numeric"
    assert amount_profile.null_count == 1
    assert amount_profile.stats.min == 10.5
    assert amount_profile.stats.max == 20.0

    cat_profile = next(p for p in profiles if p.column_name == "category")
    assert cat_profile.inferred_type == "categorical"
    assert cat_profile.unique_count == 2
