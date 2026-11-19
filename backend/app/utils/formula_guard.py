import pandas as pd

FORMULA_PREFIXES = ('=', '+', '-', '@', '\t', '\r')

def sanitize_cell_value(val: object) -> object:
    if isinstance(val, str) and val.startswith(FORMULA_PREFIXES):
        # Prepend apostrophe to neutralize spreadsheet formula evaluation
        return "'" + val
    return val

def sanitize_dataframe_for_export(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies CSV formula injection protection across all string columns in the DataFrame.
    """
    sanitized_df = df.copy()
    for col in sanitized_df.columns:
        if pd.api.types.is_object_dtype(sanitized_df[col]) or pd.api.types.is_string_dtype(sanitized_df[col]):
            sanitized_df[col] = sanitized_df[col].apply(sanitize_cell_value)
    return sanitized_df
