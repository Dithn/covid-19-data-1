import pandas as pd


def make_monotonic(df: pd.DataFrame, max_removed_rows=10) -> pd.DataFrame:
    # Forces time series to become monotonic.
    # The algorithm assumes that the most recent values are the correct ones,
    # and therefore removes previous higher values.
    n_rows_before = len(df)
    dates_before = set(df.Date)
    df_before = df.copy()

    df = df.sort_values("Date")
    metrics = ("Cumulative total",)
    for metric in metrics:
        while not df[metric].ffill().fillna(0).is_monotonic:
            diff = df[metric].ffill().shift(-1) - df[metric].ffill()
            df = df[(diff >= 0) | (diff.isna())]
    dates_now = set(df.Date)

    if max_removed_rows is not None:
        num_removed_rows = n_rows_before - len(df)
        if num_removed_rows > max_removed_rows:
            dates_wrong = dates_before.difference(dates_now)
            df_wrong = df_before[df_before.Date.isin(dates_wrong)]
            raise Exception(
                f"{num_removed_rows} rows have been removed. That is more than maximum allowed ({max_removed_rows}) by"
                f" make_monotonic() - check the data. Check \n{df_wrong}"  # {', '.join(sorted(dates_wrong))}"
            )
    return df
