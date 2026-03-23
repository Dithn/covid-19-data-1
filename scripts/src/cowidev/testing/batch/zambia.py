"""Constructs daily time series of COVID-19 testing data for Zambia.
ArcGIS Dashboard: https://zambia-open-data-nsdi-mlnr.hub.arcgis.com/pages/zambia-covid19
"""

import datetime
import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.testing.utils import make_monotonic
from cowidev.utils.web import request_json

COUNTRY = "Zambia"
UNITS = "tests performed"
TESTING_TYPE = "PCR only"
SOURCE_LABEL = "Government of Zambia"
SOURCE_URL = "https://zambia-open-data-nsdi-mlnr.hub.arcgis.com/pages/zambia-covid19"
DATA_URL = "https://services9.arcgis.com/ZNWWwa7zEkUIYLEA/arcgis/rest/services/service_d73fa15b0b304945a52e048ed42028a9/FeatureServer/0/query"
PARAMS = {
    "f": "json",
    "where": "reportdt>=timestamp '2020-01-01 00:00:00'",
    "returnGeometry": False,
    "spatialRel": "esriSpatialRelIntersects",
    "outFields": "*",
    "orderByFields": "reportdt asc",
    "resultOffset": 0,
    "resultRecordCount": 32000,
    "resultType": "standard",
    "cacheHint": True,
}


class Zambia(CountryTestBase):
    location: str = "Zambia"

    def get_data(self) -> pd.DataFrame:
        json_data = request_json(DATA_URL, params=PARAMS)
        df = pd.DataFrame([feat["attributes"] for feat in json_data["features"]])
        df["reportdt"] = df["reportdt"].astype(int).apply(lambda dt: datetime.datetime.utcfromtimestamp(dt / 1000))
        df = df.rename(columns={"totalTests": "Cumulative total"})
        df["Cumulative total"] = df["Cumulative total"].astype(int)
        # KLUDGE: there are a few days with two reports on the same day (but at
        # different times, like 10am vs 10pm). Upon inspection, it appears that the
        # latter reports (e.g. the 10pm reports) actually correspond to official cumulative
        # totals for the subsequent day (as determined by comparing to official updates
        # published on Twitter and Facebook). So I increment the date of these latter
        # reports by one.
        df = df.sort_values("reportdt")
        duplicate_idx = df.index[df["reportdt"].dt.date.duplicated(keep="first")]
        for idx in duplicate_idx:
            df.loc[idx, "reportdt"] = df.loc[idx, "reportdt"] + datetime.timedelta(days=1)
        df["Date"] = df["reportdt"].dt.strftime("%Y-%m-%d")
        df = df[["Date", "Cumulative total"]]
        df = df[df["Cumulative total"] > 0]
        df = df.groupby("Cumulative total", as_index=False).min()
        df = df.groupby("Date", as_index=False).min()
        # manual fix: drop incorrect data point on 2021-10-30
        df = df.drop(index=df[df["Date"] == "2021-10-30"].index.values)
        df = df.drop(index=df[df["Date"] == "2022-04-03"].index.values)
        df = make_monotonic(df)
        return df

    def export(self) -> None:
        df = self.get_data()
        df = df.sort_values("Date")
        df["Country"] = COUNTRY
        df["Units"] = UNITS
        df["Source URL"] = SOURCE_URL
        df["Source label"] = SOURCE_LABEL
        df["Notes"] = pd.NA
        df = df[
            [
                "Country",
                "Units",
                "Date",
                "Cumulative total",
                "Source URL",
                "Source label",
                "Notes",
            ]
        ]
        self.export_datafile(df)


def main():
    Zambia().export()
