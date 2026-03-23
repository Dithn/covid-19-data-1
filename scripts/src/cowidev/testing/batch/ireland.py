"""Constructs daily time series of COVID-19 testing data for Ireland.

Dashboard: https://covid19ireland-geohive.hub.arcgis.com/pages/hospitals-icu--testing

"""

import json
import requests
import datetime
import pandas as pd

from cowidev.testing import CountryTestBase


class Ireland(CountryTestBase):
    location = "Ireland"
    units = "tests performed"
    TESTING_TYPE = "PCR only"
    source_label = "Government of Ireland"
    source_url_ref = "https://covid19ireland-geohive.hub.arcgis.com/pages/hospitals-icu--testing"
    source_url = "https://services-eu1.arcgis.com/z6bHNio59iTqqSUY/arcgis/rest/services/LaboratoryLocalTimeSeriesHistoricView/FeatureServer/0/query"
    rename_columns = {
        "Date_HPSC": "Date",
        "Test24": "Daily change in cumulative total",
        "TotalLabs": "Cumulative total",
        "PosR7": "Positive rate",
    }

    def read(self):
        DATE_COL = "Date_HPSC"
        params = {
            "f": "json",
            "where": f"{DATE_COL}>'2020-01-01 00:00:00'",  # "Dates>'2020-01-01 00:00:00'",
            "returnGeometry": False,
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": f"{DATE_COL},TotalLabs,Test24,PosR7",
            "orderByFields": f"{DATE_COL} asc",
            "resultOffset": 0,
            "resultRecordCount": 32000,
            "resultType": "standard",
        }
        res = requests.get(self.source_url, params=params)
        json_data = json.loads(res.text)
        df = pd.DataFrame([d["attributes"] for d in json_data["features"]])
        return df

    def pipe_date(self, df: pd.DataFrame):
        df["Date"] = df["Date"].astype(int).apply(lambda dt: datetime.datetime.utcfromtimestamp(dt / 1000))
        df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
        return df

    def pipeline(self, df: pd.DataFrame):
        df = df.pipe(self.pipe_rename_columns)
        df = df.pipe(self.pipe_date)
        # drops duplicate YYYY-MM-DD rows.
        # df[df[DATE_COL].dt.strftime('%Y-%m-%d').duplicated(keep=False)]  # prints out rows with duplicate YYYY-MM-DD value
        # df.sort_values(DATE_COL, inplace=True)
        # df.drop_duplicates(subset=['Date'], keep='last', inplace=True)

        df = df[["Date", "Cumulative total", "Positive rate"]]
        df = df.sort_values("Date").dropna(subset=["Date", "Cumulative total", "Positive rate"], how="any")
        df["Cumulative total"] = df["Cumulative total"].astype(int)
        df["Positive rate"] = (df["Positive rate"].astype(int)).div(100)
        df = df.pipe(self.pipe_metadata)
        return df

    def export(self) -> None:
        df = self.read().pipe(self.pipeline)
        sanity_checks(df)
        self.export_datafile(df)
        return None


def sanity_checks(df: pd.DataFrame) -> None:
    """checks that there are no obvious errors in the scraped data."""
    df_temp = df.copy()
    # checks that the max date is less than tomorrow's date.
    assert datetime.datetime.strptime(df_temp["Date"].max(), "%Y-%m-%d") < (
        datetime.datetime.utcnow() + datetime.timedelta(days=1)
    )
    # checks that there are no duplicate dates
    assert df_temp["Date"].duplicated().sum() == 0, "One or more rows share the same date."
    if "Cumulative total" not in df_temp.columns:
        df_temp["Cumulative total"] = df_temp["Daily change in cumulative total"].cumsum()
    # checks that the cumulative number of tests on date t is always greater than the figure for t-1:
    assert (
        df_temp["Cumulative total"].iloc[1:] >= df_temp["Cumulative total"].shift(1).iloc[1:]
    ).all(), "On one or more dates, `Cumulative total` is greater on date t-1."
    return None


def main():
    Ireland().export()
