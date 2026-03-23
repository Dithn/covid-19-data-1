import os
from datetime import datetime

import pandas as pd
import requests
from uk_covid19 import Cov19API

from cowidev import PATHS

DATASET_NAME = "uk_covid_data"
OUTPUT_CSV = os.path.join(PATHS.INTERNAL_GRAPHER_DIR, f"{DATASET_NAME}.csv")
ZERO_DAY = "2020-01-01"


def get_uk() -> pd.DataFrame:
    # Absolute
    filters = ["areaType=overview"]
    structure = {
        "Year": "date",
        "Country": "areaName",
        "areaCode": "areaCode",
        "weekly_cases_rolling": "newCasesByPublishDateRollingSum",
        "cumulative_cases": "cumCasesByPublishDate",
        "weekly_deaths_rolling": "newDeaths28DaysByPublishDateRollingSum",
        "cumulative_deaths": "cumDeaths28DaysByPublishDate",
        "daily_deaths": "newDeaths28DaysByPublishDate",
        "daily_cases": "newCasesByPublishDate",
        "test_positivity_rate": "uniqueCasePositivityBySpecimenDateRollingSum",
        "weekly_hospital_admissions": "newAdmissionsRollingSum",
        "people_in_hospital": "hospitalCases",
        "people_ventilated": "covidOccupiedMVBeds",
    }
    api = Cov19API(filters=filters, structure=structure)
    uk = api.get_dataframe()

    # Rate
    filters = ["areaType=overview"]
    structure = {
        "Year": "date",
        "Country": "areaName",
        "areaCode": "areaCode",
        "cumulative_cases_rate": "cumCasesByPublishDateRate",
        "cumulative_deaths_rate": "cumDeaths28DaysByPublishDateRate",
        "weekly_cases_rate": "newCasesBySpecimenDateRollingRate",
        "weekly_deaths_rate": "newDeaths28DaysByDeathDateRollingRate",
    }
    api = Cov19API(filters=filters, structure=structure)
    uk_rate = api.get_dataframe()

    # Merge
    return pd.merge(uk, uk_rate)


def find_metric_peak(df: pd.DataFrame, metric: str, period_start="2020-12-09", period_end="2021-02-23") -> tuple:
    period_df = df[(df.Year >= period_start) & (df.Year <= period_end)][["Year", metric]]
    period_df = period_df.sort_values(metric, ascending=False, na_position="last")
    peak_date = period_df.Year.values[0]
    peak_value = period_df[metric].values[0]
    return peak_date, peak_value


def add_decoupling_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if df.people_ventilated.isnull().all() or df.weekly_cases_rolling.isnull().all():
        df[
            [
                "weekly_cases_rolling_normalized",
                "people_in_hospital_normalized",
                "people_ventilated_normalized",
                "weekly_deaths_rolling_normalized",
            ]
        ] = pd.NA
        return df

    case_peak_date, case_peak_value = find_metric_peak(df, "weekly_cases_rolling")
    hosp_peak_date, hosp_peak_value = find_metric_peak(df, "people_in_hospital")
    icu_peak_date, icu_peak_value = find_metric_peak(df, "people_ventilated")
    death_peak_date, death_peak_value = find_metric_peak(df, "weekly_deaths_rolling")

    hosp_shift = (pd.to_datetime(hosp_peak_date) - pd.to_datetime(case_peak_date)).days
    icu_shift = (pd.to_datetime(icu_peak_date) - pd.to_datetime(case_peak_date)).days
    death_shift = (pd.to_datetime(death_peak_date) - pd.to_datetime(case_peak_date)).days

    df["weekly_cases_rolling_normalized"] = (df.weekly_cases_rolling / case_peak_value).mul(100).round(2)
    df["people_in_hospital_normalized"] = (df.people_in_hospital.shift(hosp_shift) / hosp_peak_value).mul(100).round(2)
    df["people_ventilated_normalized"] = (df.people_ventilated.shift(icu_shift) / icu_peak_value).mul(100).round(2)
    df["weekly_deaths_rolling_normalized"] = (
        (df.weekly_deaths_rolling.shift(death_shift) / death_peak_value).mul(100).round(2)
    )
    return df


def get_nation() -> pd.DataFrame:
    # Absolute
    filters = ["areaType=nation"]
    structure = {
        "Year": "date",
        "Country": "areaName",
        "areaCode": "areaCode",
        "cumulative_cases": "cumCasesByPublishDate",
        "cumulative_deaths": "cumDeaths28DaysByPublishDate",
        "weekly_cases_rolling": "newCasesByPublishDateRollingSum",
        "weekly_deaths_rolling": "newDeaths28DaysByPublishDateRollingSum",
        "daily_deaths": "newDeaths28DaysByPublishDate",
        "daily_cases": "newCasesByPublishDate",
        "test_positivity_rate": "uniqueCasePositivityBySpecimenDateRollingSum",
        "weekly_hospital_admissions": "newAdmissionsRollingSum",
        "people_in_hospital": "hospitalCases",
        "people_ventilated": "covidOccupiedMVBeds",
    }
    api = Cov19API(filters=filters, structure=structure)
    nation = api.get_dataframe()

    # Rate
    filters = ["areaType=nation"]
    structure = {
        "Year": "date",
        "Country": "areaName",
        "areaCode": "areaCode",
        "cumulative_cases_rate": "cumCasesByPublishDateRate",
        "cumulative_deaths_rate": "cumDeaths28DaysByPublishDateRate",
        "weekly_cases_rate": "newCasesBySpecimenDateRollingRate",
        "weekly_deaths_rate": "newDeaths28DaysByDeathDateRollingRate",
    }
    api = Cov19API(filters=filters, structure=structure)
    nation_rate = api.get_dataframe()

    # Merge
    return pd.merge(nation, nation_rate)


def get_local() -> pd.DataFrame:
    # Absolute
    filters = ["areaType=utla"]
    metrics = {
        "Year": "date",
        "Country": "areaName",
        "areaCode": "areaCode",
        "cumulative_cases": "cumCasesByPublishDate",
        "cumulative_deaths": "cumDeaths28DaysByPublishDate",
        "weekly_cases_rolling": "newCasesByPublishDateRollingSum",
        "weekly_deaths_rolling": "newDeaths28DaysByPublishDateRollingSum",
        "daily_deaths": "newDeaths28DaysByPublishDate",
        "daily_cases": "newCasesByPublishDate",
        "test_positivity_rate": "uniqueCasePositivityBySpecimenDateRollingSum",
    }
    api = Cov19API(filters=filters, structure=metrics)
    local = api.get_dataframe().sort_values("Year")

    # Rate
    url_local_rate = (
        "https://api.coronavirus.data.gov.uk/v2/data?areaType=utla&metric=cumCasesByPublishDateRate&"
        "metric=cumDeaths28DaysByPublishDateRate&metric=newCasesBySpecimenDateRollingRate&"
        "metric=newDeaths28DaysByDeathDateRollingRate"
    )
    local_rate = requests.get(url_local_rate).json()
    local_rate = pd.DataFrame.from_records(local_rate["body"], exclude=["areaType"])
    local_rate = local_rate.rename(
        columns={
            "areaName": "Country",
            "date": "Year",
            "cumCasesByPublishDateRate": "cumulative_cases_rate",
            "cumDeaths28DaysByPublishDateRate": "cumulative_deaths_rate",
            "newCasesBySpecimenDateRollingRate": "weekly_cases_rate",
            "newDeaths28DaysByDeathDateRollingRate": "weekly_deaths_rate",
        }
    )

    # Merge
    return pd.merge(local, local_rate)


def get_nhs_region() -> pd.DataFrame:
    filters = ["areaType=nhsRegion"]
    metrics = {
        "Year": "date",
        "Country": "areaName",
        "areaCode": "areaCode",
        "weekly_hospital_admissions": "newAdmissionsRollingSum",
        "people_in_hospital": "hospitalCases",
    }
    api = Cov19API(filters=filters, structure=metrics)
    return api.get_dataframe()


def get_day_diff(dt):
    return (datetime.strptime(dt, "%Y-%m-%d") - datetime.strptime(ZERO_DAY, "%Y-%m-%d")).days


def generate_dataset():
    combined = pd.concat([get_uk(), get_nation(), get_local(), get_nhs_region()])
    combined = combined.drop_duplicates(subset=["Country", "Year"], keep="first")

    combined = combined.groupby("Country").apply(add_decoupling_metrics)

    combined["daily_cases_rolling_average"] = combined["weekly_cases_rolling"] / 7
    combined["daily_deaths_rolling_average"] = combined["weekly_deaths_rolling"] / 7
    combined["daily_cases_rate_rolling_average"] = combined["weekly_cases_rate"] / 7
    combined["daily_deaths_rate_rolling_average"] = combined["weekly_deaths_rate"] / 7
    combined["new_hospital_admissions"] = combined["weekly_hospital_admissions"] / 7

    combined["Year"] = combined["Year"].apply(get_day_diff)

    combined = combined[["Country"] + [col for col in combined.columns if col != "Country"]]
    combined = (
        combined.dropna(how="any", subset=["weekly_cases_rolling"])
        .drop(columns="areaCode")
        .sort_values(["Country", "Year"])
    )

    # Export
    combined.to_csv(OUTPUT_CSV, index=False)


if __name__ == "__main__":
    generate_dataset()
