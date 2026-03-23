import pandas as pd

from cowidev.utils.clean.strings import clean_string


def clean_column_name(colname: str):
    """Clean column name."""
    if pd.isnull(colname):
        colname_new = ""
    else:
        colname_new = clean_string(colname)
    if "Unnamed:" in colname_new:
        colname_new = ""
    return colname_new


def clean_df_columns_multiindex(df: pd.DataFrame):
    columns_new = []
    for col in df.columns:
        columns_new.append([clean_column_name(c) for c in col])
    df.columns = pd.MultiIndex.from_tuples(columns_new)
    return df
