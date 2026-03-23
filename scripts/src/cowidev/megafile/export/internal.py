import os

import pandas as pd
import numpy as np

from cowidev.megafile.export.annotations import AnnotatorInternal, add_annotations_countries_100_percentage
from cowidev.utils.utils import dict_to_compact_json


COUNTRIES_WITH_PARTLY_VAX_METRIC = []


def country_vax_data_partly(country_data):
    return [os.path.join(country_data, f"{country}.csv") for country in COUNTRIES_WITH_PARTLY_VAX_METRIC]


internal_files_columns = {
    "cases-tests": {
        "columns": [
            "location",
            "date",
            "total_cases",
            "new_cases",
            "new_cases_smoothed",
            "total_cases_per_million",
            "new_cases_per_million",
            "new_cases_smoothed_per_million",
            "reproduction_rate",
            "new_tests",
            "total_tests",
            "total_tests_per_thousand",
            "new_tests_per_thousand",
            "new_tests_smoothed",
            "new_tests_smoothed_per_thousand",
            "positive_rate",
            "tests_per_case",
            "tests_units",
            "share_cases_sequenced",
            "stringency_index",
        ],
        "dropna": "all",
    },
    "stringency": {
        "columns": [
            "location",
            "date",
            "stringency_index",
            "stringency_index_nonvac",
            "stringency_index_vac",
            "stringency_index_weighted_avg",
        ],
        "dropna": "all",
    },
    "deaths": {
        "columns": [
            "continent",
            "location",
            "date",
            "total_deaths",
            "total_deaths_per_million",
            "total_deaths_last12m",
            "total_deaths_last12m_per_million",
            "new_deaths",
            "new_deaths_per_million",
            "new_deaths_smoothed",
            "new_deaths_smoothed_per_million",
            "cfr",
            "cfr_short_term",
        ],
        "dropna": "all",
    },
    "vaccinations": {
        "columns": [
            "location",
            "date",
            "total_vaccinations",
            "people_vaccinated",
            "people_fully_vaccinated",
            "total_boosters",
            "new_vaccinations",
            "new_vaccinations_smoothed",
            "total_vaccinations_per_hundred",
            "people_vaccinated_per_hundred",
            "people_fully_vaccinated_per_hundred",
            "total_boosters_per_hundred",
            "new_vaccinations_smoothed_per_million",
            "population",
            "people_partly_vaccinated",
            "people_partly_vaccinated_per_hundred",
            "new_people_vaccinated_smoothed",
            "new_people_vaccinated_smoothed_per_hundred",
            "rolling_vaccinations_6m",
            "rolling_vaccinations_6m_per_hundred",
            "rolling_vaccinations_9m",
            "rolling_vaccinations_9m_per_hundred",
            "rolling_vaccinations_12m",
            "rolling_vaccinations_12m_per_hundred",
        ],
        "dropna": "all",
    },
    "vaccinations-bydose": {
        "columns": [
            "location",
            "date",
            "people_fully_vaccinated",
            "people_fully_vaccinated_per_hundred",
            "people_partly_vaccinated",
            "people_partly_vaccinated_per_hundred",
        ],
        "dropna": "any",
    },
    "vaccinations-boosters": {
        "columns": [
            "location",
            "date",
            "total_vaccinations_no_boosters",
            "total_vaccinations_no_boosters_per_hundred",
            "total_boosters",
            "total_boosters_per_hundred",
        ],
        "dropna": "any",
    },
    "hospital-admissions": {
        "columns": [
            "location",
            "date",
            "icu_patients",
            "icu_patients_per_million",
            "hosp_patients",
            "hosp_patients_per_million",
            "weekly_icu_admissions",
            "weekly_icu_admissions_per_million",
            "weekly_hosp_admissions",
            "weekly_hosp_admissions_per_million",
        ],
        "dropna": "all",
    },
    "excess-mortality": {
        "columns": [
            "location",
            "date",
            "excess_mortality",  # perc_week
            "excess_mortality_cumulative",  # perc_cum
            "excess_mortality_cumulative_absolute",  # count_cum
            "excess_mortality_cumulative_per_million",  # count_cum_pm
            "excess_mortality_count_week",
            "excess_mortality_count_week_pm",
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
            # TODO https://github.com/owid/owid-issues/issues/553
            "excess_mortality_cumulative_absolute_last12m",
            "excess_mortality_cumulative_absolute_last12m_per_million",
            "cumulative_estimated_daily_excess_deaths_last12m",
            "cumulative_estimated_daily_excess_deaths_last12m_per_100k",
            "cumulative_estimated_daily_excess_deaths_ci_95_top_last12m",
            "cumulative_estimated_daily_excess_deaths_ci_95_top_last12m_per_100k",
            "cumulative_estimated_daily_excess_deaths_ci_95_bot_last12m",
            "cumulative_estimated_daily_excess_deaths_ci_95_bot_last12m_per_100k",
            # Add confirmed deaths so we can plot them together in the Explorer
            "total_deaths",
            "total_deaths_per_million",
            "total_deaths_last12m",
            "total_deaths_last12m_per_million",
            "new_deaths_smoothed",
            "new_deaths_smoothed_per_million",
        ],
        "dropna": "all",
    },
    "auxiliary": {
        "columns": [
            "iso_code",
            "continent",
            "location",
            "date",
            "population_density",
            "median_age",
            "aged_65_older",
            "aged_70_older",
            "gdp_per_capita",
            "extreme_poverty",
            "cardiovasc_death_rate",
            "diabetes_prevalence",
            "female_smokers",
            "male_smokers",
            "handwashing_facilities",
            "hospital_beds_per_thousand",
            "life_expectancy",
            "human_development_index",
        ],
        "dropna": "all",
    },
    "all-reduced": {
        "columns": [
            "location",
            "date",
            "total_vaccinations_per_hundred",
            "people_vaccinated_per_hundred",
            "people_fully_vaccinated_per_hundred",
            "total_boosters_per_hundred",
            "new_cases_smoothed_per_million",
            "new_deaths_smoothed_per_million",
            "weekly_hosp_admissions_per_million",
            "icu_patients_per_million",
            "new_tests_smoothed_per_thousand",
            "positive_rate",
            "reproduction_rate",
            "new_deaths_smoothed",
            "total_deaths_per_million",
            "excess_mortality_cumulative_per_million",  # count_cum_pm
            "total_deaths",
            "excess_mortality_cumulative_absolute",
        ],
        "dropna": "all",
    },
}


def create_internal(
    df: pd.DataFrame, output_dir: str, annotations_path: str, country_data: str, logger, categories_filter=None
):
    # Ensure internal/ dir is created
    os.makedirs(output_dir, exist_ok=True)

    # These are "key" or "attribute" columns.
    # These columns are ignored when dropping rows with dropna().
    non_value_columns = ["iso_code", "continent", "location", "date", "population"]

    # Load annotations
    annotator = AnnotatorInternal.from_yaml(annotations_path, logger)

    # Copy df
    df = df.copy()

    # Add new annotations for countries having >100% per-capita metric values (runtime, not stored in ANNOTATIONS_PATH)
    annotator = add_annotations_countries_100_percentage(df, annotator)
    # Insert CFR column to avoid calculating it on the client, and enable
    # splitting up into cases & deaths columns.
    df["cfr"] = (df["total_deaths"] * 100 / df["total_cases"]).round(3).replace([np.inf, -np.inf], np.nan)

    # Insert short-term CFR
    cfr_day_shift = 10  # We compute number of deaths divided by number of cases `cfr_day_shift` days before.
    shifted_cases = df.sort_values("date").groupby("location")["new_cases_smoothed"].shift(cfr_day_shift)
    df["cfr_short_term"] = (
        df["new_deaths_smoothed"].div(shifted_cases).replace(np.inf, np.nan).replace(-np.inf, np.nan).mul(100).round(4)
    )

    df.loc[
        (df.cfr_short_term < 0) | (df.cfr_short_term > 10) | (df.date.astype(str) < "2020-09-01"),
        "cfr_short_term",
    ] = np.nan

    # Add partly vaccinated
    df = df.pipe(add_partially_vaccinated, country_data)
    # Add total vaccinations without boosters
    df = df.pipe(add_total_vaccinations_no_boosters)

    # Replace pd.NA with np.nan
    df = df.replace({pd.NA: np.nan})

    def _export_internal(output_dir, name, config, annotator):
        output_path = os.path.join(output_dir, f"megafile--{name}.json")
        value_columns = list(set(config["columns"]) - set(non_value_columns))
        df_output = df[config["columns"]]
        if name == "vaccinations-boosters":
            df_output = df_output.copy().pipe(fillna_boosters_till_valid)
        df_output = df_output.dropna(subset=value_columns, how=config["dropna"])
        df_output = annotator.add_annotations(df_output, name)
        df_to_columnar_json(df_output, output_path)

    # Export
    for name, config in internal_files_columns.items():
        if categories_filter:
            if name in categories_filter:
                _export_internal(output_dir, name, config, annotator)
        else:
            _export_internal(output_dir, name, config, annotator)


def add_partially_vaccinated(df: pd.DataFrame, country_data: str):
    # Countries that already have partially vaxxed metric
    df_a = df[df.location.isin(COUNTRIES_WITH_PARTLY_VAX_METRIC)]
    for filename in country_vax_data_partly(country_data):
        if not os.path.isfile(filename):
            raise ValueError(f"Invalid file path! {filename}")
        try:
            x = pd.read_csv(filename, usecols=["location", "date", "people_partly_vaccinated"])
        except ValueError as e:
            raise ValueError(f"{filename}: {e}")
        df_a = df_a.merge(x, on=["location", "date"], how="outer")
    df_b = df[~df.location.isin(COUNTRIES_WITH_PARTLY_VAX_METRIC)]
    df_b.loc[:, "people_partly_vaccinated"] = df_b.people_vaccinated - df_b.people_fully_vaccinated
    df = pd.concat([df_a, df_b], ignore_index=True).sort_values(["location", "date"])
    df.loc[:, "people_partly_vaccinated_per_hundred"] = df["people_partly_vaccinated"] / df["population"] * 100
    df.loc[df.location == "United States", "people_partly_vaccinated_per_hundred"] = (
        df["people_partly_vaccinated"] / 336324782 * 100
    )
    return df


def add_fully_vaccinated_no_boosters(df):
    return df.assign(
        people_fully_vaccinated_no_booster=df.people_fully_vaccinated - df.total_boosters.fillna(0),
        people_fully_vaccinated_no_booster_per_hundred=(
            df.people_fully_vaccinated_per_hundred - df.total_boosters_per_hundred.fillna(0)
        ),
    )


def add_total_vaccinations_no_boosters(df):
    return df.assign(
        total_vaccinations_no_boosters=df.total_vaccinations - df.total_boosters.fillna(0),
        total_vaccinations_no_boosters_per_hundred=(
            df.total_vaccinations_per_hundred - df.total_boosters_per_hundred.fillna(0)
        ),
    )


def fillna_boosters_till_valid(df):
    # Fill NaNs in total_boosters (only up to first valid value)
    df = df.sort_values(["location", "date"])
    msk = df.groupby(["location"]).total_boosters.ffill().isna()
    df.loc[msk, ["total_boosters", "total_boosters_per_hundred"]] = 0
    return df


def df_to_columnar_json(complete_dataset, output_path):
    """Writes a columnar JSON version of the complete dataset.

    NA values are dropped from the output.

    In columnar JSON, the table headers are keys, and the values are lists
    of all cells for a column.

    Example:
        {
            "iso_code": ["AFG", "AFG", ... ],
            "date": ["2020-03-01", "2020-03-02", ... ]
        }
    """
    # Replace NaNs with None in order to be serializable to JSON.
    # JSON doesn't support NaNs, but it does have null which is represented as None in Python.
    columnar_dict = complete_dataset.to_dict(orient="list")
    for k, v in columnar_dict.items():
        columnar_dict[k] = [x if pd.notnull(x) else None for x in v]
    with open(output_path, "w") as file:
        file.write(dict_to_compact_json(columnar_dict))
