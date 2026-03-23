import os
from datetime import datetime

import pandas as pd

from cowidev import PATHS
from cowidev.utils.clean.dates import DATE_FORMAT
from cowidev.utils.log import get_logger
from cowidev.utils.utils import export_timestamp

ZERO_DAY = "2020-01-21"
zero_day = datetime.strptime(ZERO_DAY, DATE_FORMAT)

URL_VACCINE = "https://raw.githubusercontent.com/OxCGRT/covid-policy-tracker/master/data/OxCGRT_vaccines_full.csv"
DATA_HOSP_GRAPHER_FILE = os.path.join(PATHS.INTERNAL_GRAPHER_DIR, "COVID-2019 - Hospital & ICU.csv")

logger = get_logger()


def _owid_format(df):
    print("Reshaping to OWID format…")
    df.loc[:, "value"] = df["value"].round(3)
    df = df.drop(columns="iso_code")

    # Data cleaning
    df = df[-df["indicator"].str.contains("Weekly new plot admissions")]
    df["date"] = df.date.astype(str).str.slice(0, 10)
    df = df.groupby(["entity", "date", "indicator"], as_index=False).max()

    df = df.pivot_table(index=["entity", "date"], columns="indicator").value.reset_index()
    df = df.rename(columns={"entity": "Country"})
    return df


def _date_to_owid_year(df):
    print("Converting dates to grapher years…")
    df.loc[:, "date"] = (pd.to_datetime(df.date, format="%Y-%m-%d") - zero_day).dt.days
    df = df.rename(columns={"date": "Year"})
    return df


def run_grapheriser():
    df = pd.read_csv(PATHS.DATA_HOSP_MAIN_FILE)
    df = df.pipe(_owid_format).pipe(_date_to_owid_year)
    df = df.drop_duplicates(keep=False, subset=["Country", "Year"])
    df.to_csv(DATA_HOSP_GRAPHER_FILE, index=False)
    export_timestamp(PATHS.DATA_TIMESTAMP_HOSP_FILE)
