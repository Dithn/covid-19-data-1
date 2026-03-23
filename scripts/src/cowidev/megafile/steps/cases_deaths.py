import datetime
import os
from functools import reduce
import pandas as pd


def get_casedeath(dataset_dir: str):
    """
    Reads each COVID-19 Cases/Deaths dataset located in `dataset_dir`.
    Melts the dataframe to vertical format (1 row per country and date).
    Merges all dataframes into one with outer joins.

    Returns:
        df {dataframe}
    """

    varnames = [
        "total_cases",
        "new_cases",
        "weekly_cases",
        "total_deaths",
        "new_deaths",
        "weekly_deaths",
        "total_cases_per_million",
        "new_cases_per_million",
        "weekly_cases_per_million",
        "total_deaths_per_million",
        "new_deaths_per_million",
        "weekly_deaths_per_million",
    ]

    data_frames = []

    # Process each file and melt it to vertical format
    for varname in varnames:
        tmp = pd.read_csv(os.path.join(dataset_dir, f"{varname}.csv"))
        country_cols = list(tmp.columns)
        country_cols.remove("date")

        # Carrying last observation forward for International totals to avoid discrepancies
        if varname[:5] == "total":
            tmp = tmp.sort_values("date")
            if "International" in tmp.columns:
                tmp["International"] = tmp["International"].ffill()

        tmp = (
            pd.melt(tmp, id_vars="date", value_vars=country_cols)
            .rename(columns={"value": varname, "variable": "location"})
            .dropna()
        )

        if varname[:7] == "weekly_":
            tmp[varname] = tmp[varname].div(7).round(3)
            tmp = tmp.rename(
                errors="ignore",
                columns={
                    "weekly_cases": "new_cases_smoothed",
                    "weekly_deaths": "new_deaths_smoothed",
                    "weekly_cases_per_million": "new_cases_smoothed_per_million",
                    "weekly_deaths_per_million": "new_deaths_smoothed_per_million",
                },
            )
        else:
            tmp[varname] = tmp[varname].round(3)
        data_frames.append(tmp)

    # Outer join between all files
    df = reduce(
        lambda left, right: pd.merge(left, right, on=["date", "location"], how="outer"),
        data_frames,
    )

    return df


def add_cumulative_deaths_last12m(df: pd.DataFrame) -> pd.DataFrame:

    df["daily_diff"] = df[["location", "total_deaths"]].groupby("location").fillna(0).diff()
    date_cutoff = pd.to_datetime(df.date.max()) - datetime.timedelta(days=365.2425)
    df.loc[pd.to_datetime(df.date) < date_cutoff, "daily_diff"] = 0

    df["total_deaths_last12m"] = df[["location", "daily_diff"]].groupby("location").cumsum()
    df.loc[(pd.to_datetime(df.date) < date_cutoff) | (df.new_deaths.isnull()), "total_deaths_last12m"] = pd.NA
    df["total_deaths_last12m_per_million"] = df.total_deaths_last12m.mul(1000000).div(df.population)

    return df.drop(columns="daily_diff")
