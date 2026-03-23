import pandas as pd
import numpy as np
import datetime


def add_excess_mortality(df: pd.DataFrame, wmd_hmd_file: str, economist_file: str) -> pd.DataFrame:

    # XM data from HMD & WMD
    column_mapping = {
        "p_proj_all_ages": "excess_mortality",  # excess_mortality_perc_weekly
        "cum_p_proj_all_ages": "excess_mortality_cumulative",  # excess_mortality_perc_cum
        "cum_excess_proj_all_ages": "excess_mortality_cumulative_absolute",  # excess_mortality_count_cum
        "cum_excess_per_million_proj_all_ages": "excess_mortality_cumulative_per_million",  # excess_mortality_count_cum_pm
        "excess_proj_all_ages": "excess_mortality_count_week",  # excess_mortality_count_week
        "excess_per_million_proj_all_ages": "excess_mortality_count_week_pm",  # excess_mortality_count_week_pm
    }
    wmd_hmd = pd.read_csv(wmd_hmd_file, usecols=["location", "date"] + list(column_mapping.keys()))
    df = df.merge(wmd_hmd, how="left", on=["location", "date"]).rename(columns=column_mapping)

    # XM data from The Economist
    econ = pd.read_csv(
        economist_file,
        usecols=[
            "country",
            "date",
            "cumulative_estimated_daily_excess_deaths",
            "cumulative_estimated_daily_excess_deaths_ci_95_top",
            "cumulative_estimated_daily_excess_deaths_ci_95_bot",
            "cumulative_estimated_daily_excess_deaths_per_100k",
            "cumulative_estimated_daily_excess_deaths_ci_95_top_per_100k",
            "cumulative_estimated_daily_excess_deaths_ci_95_bot_per_100k",
            "estimated_daily_excess_deaths",
            "estimated_daily_excess_deaths_ci_95_top",
            "estimated_daily_excess_deaths_ci_95_bot",
            "estimated_daily_excess_deaths_per_100k",
            "estimated_daily_excess_deaths_ci_95_top_per_100k",
            "estimated_daily_excess_deaths_ci_95_bot_per_100k",
        ],
    ).rename(columns={"country": "location"})
    df = df.merge(econ, how="left", on=["location", "date"])

    # Add last 12m
    df = _add_last12m_to_metric(df, "excess_mortality_cumulative_absolute", "location", 1000000, "per_million")
    df = _add_last12m_to_metric(df, "cumulative_estimated_daily_excess_deaths", "location", 100000, "per_100k")
    df = _add_last12m_to_metric(
        df, "cumulative_estimated_daily_excess_deaths_ci_95_top", "location", 100000, "per_100k"
    )
    df = _add_last12m_to_metric(
        df, "cumulative_estimated_daily_excess_deaths_ci_95_bot", "location", 100000, "per_100k"
    )
    # print(df.columns)
    return df


def _add_last12m_to_metric(
    df: pd.DataFrame, column_metric: str, column_location: str, scaling: int, scaling_slug: str
) -> pd.DataFrame:
    column_metric_12m = f"{column_metric}_last12m"

    # Get only last 12 month of data
    date_cutoff = datetime.datetime.now() - datetime.timedelta(days=365.2425)
    # df = df[pd.to_datetime(df.date) > date_cutoff]

    # Get metric value 12 months ago
    df_tmp = (
        df[pd.to_datetime(df.date) > date_cutoff]
        .dropna(subset=[column_metric])
        .sort_values([column_location, "date"])
        .drop_duplicates(column_location)[[column_location, column_metric]]
        .rename(columns={column_metric: column_metric_12m})
    )

    # Compute the difference, obtain last12m metric
    df = df.merge(df_tmp, on=[column_location], how="left")
    values = df[column_metric] - df[column_metric_12m]

    # Assign NaN to >1 year old data
    values[pd.to_datetime(df.date) < date_cutoff] = np.nan

    # Assign to df
    df = df.assign(
        **{
            column_metric_12m: values,
            f"{column_metric_12m}_{scaling_slug}": values.mul(scaling).div(df.population),
        }
    )

    return df
