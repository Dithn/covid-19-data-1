import os
from datetime import date, timedelta

import pandas as pd

from cowidev import PATHS
from cowidev.utils.s3 import S3, obj_to_s3
from cowidev.utils.utils import dict_to_compact_json


DATA_DIR = PATHS.DATA_DIR
# Latest data will only have data up to `NUM_WEEKS_TOLERANCE_LATEST` weeks before today.
NUM_WEEKS_TOLERANCE_LATEST = 4

def create_dataset(df, macro_variables, logger, filename=None):
    """Export dataset as CSV, XLSX and JSON (complete time series)."""
    # Reduce size
    ## Integers
    cols_int = [
        "new_cases",
        "new_deaths",
        "total_cases",
        "total_deaths",
        "icu_patients",
        "hosp_patients",
        "weekly_icu_admissions",
        "weekly_hosp_admissions",
        "new_tests",
        "total_tests",
        "total_vaccinations",
        "people_vaccinated",
        "people_fully_vaccinated",
        "total_boosters",
        "new_vaccinations",
        "population",
    ]
    df[cols_int] = df[cols_int].astype("Int64")

    if filename is None:
        filename = "owid-covid-data"
    logger.info("Writing to CSV…")
    filename_local = os.path.join(DATA_DIR, f"{filename}.csv")
    df.to_csv(filename_local, index=False)
    S3().upload_to_s3(filename_local, f"s3://covid-19/public/{filename}.csv", public=True)

    ## Float resolution (only for local file)
    # cols_float = df.select_dtypes(include=['float']).columns.tolist()
    # df[cols_float] = df[cols_float].round(2)
    # df.to_csv(filename_local, index=False)

    # logger.info("Writing to XLSX…")
    # # filename = os.path.join(DATA_DIR, "owid-covid-data.xlsx")
    # # all_covid.to_excel(os.path.join(DATA_DIR, "owid-covid-data.xlsx"), index=False, engine="xlsxwriter")
    # # upload_to_s3(filename, "public/owid-covid-data.xlsx", public=True)
    # obj_to_s3(df, s3_path=f"s3://covid-19/public/{filename}.xlsx", public=True)

    # logger.info("Writing to JSON…")
    # data = df_to_dict(
    #     df,
    #     macro_variables.keys(),
    #     valid_json=True,
    # )
    # obj_to_s3(data, f"s3://covid-19/public/{filename}.json", public=True)


def create_latest(df, logger):
    """Export dataset as CSV, XLSX and JSON (latest data points)."""
    df = df[df.date >= str(date.today() - timedelta(weeks=NUM_WEEKS_TOLERANCE_LATEST))]
    df = df.sort_values("date")

    latest = [df[df.location == loc].ffill().tail(1).round(3) for loc in set(df.location)]
    latest = pd.concat(latest)
    latest = latest.sort_values("location").rename(columns={"date": "last_updated_date"})

    logger.info("Writing latest version…")
    # CSV
    latest.to_csv(os.path.join(DATA_DIR, "latest", "owid-covid-latest.csv"), index=False)
    S3().upload_to_s3(
        os.path.join(DATA_DIR, "latest", "owid-covid-latest.csv"),
        "s3://covid-19/public/latest/owid-covid-latest.csv",
        public=True,
    )
    # XLSX
    obj_to_s3(latest, s3_path="s3://covid-19/public/latest/owid-covid-latest.xlsx", public=True)
    # JSON
    latest.dropna(subset=["iso_code"]).set_index("iso_code").to_json(
        os.path.join(DATA_DIR, "latest", "owid-covid-latest.json"), orient="index"
    )
    S3().upload_to_s3(
        os.path.join(DATA_DIR, "latest", "owid-covid-latest.json"),
        "s3://covid-19/public/latest/owid-covid-latest.json",
        public=True,
    )


def df_to_dict(complete_dataset, static_columns, valid_json=False):
    """
    Writes a JSON version of the complete dataset, with the ISO code at the root.
    NA values are dropped from the output.
    Macro variables are normalized by appearing only once, at the root of each ISO code.
    """
    megajson = {}

    static_columns = ["continent", "location"] + list(static_columns)

    complete_dataset = complete_dataset.dropna(axis="rows", subset=["iso_code"])

    for iso in complete_dataset.iso_code.unique():
        country_df = complete_dataset[complete_dataset.iso_code == iso].drop(columns=["iso_code"])
        static_data = country_df.head(1)[static_columns].to_dict("records")[0]
        megajson[iso] = {k: v for k, v in static_data.items() if pd.notnull(v)}
        megajson[iso]["data"] = [
            {k: v for k, v in r.items() if pd.notnull(v)}
            for r in country_df.drop(columns=static_columns).to_dict("records")
        ]
    if valid_json:
        megajson = dict_to_compact_json(megajson)
    return megajson


def df_to_json(complete_dataset, output_path, static_columns):
    """
    Writes a JSON version of the complete dataset, with the ISO code at the root.
    NA values are dropped from the output.
    Macro variables are normalized by appearing only once, at the root of each ISO code.
    """
    megajson = df_to_dict(complete_dataset, static_columns, valid_json=True)
    with open(output_path, "w") as file:
        file.write(megajson)
