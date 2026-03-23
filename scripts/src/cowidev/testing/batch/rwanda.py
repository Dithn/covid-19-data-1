import pandas as pd

from cowidev.utils.web import request_json
from cowidev.utils.clean import clean_date_series
from cowidev.testing.utils import make_monotonic
from cowidev.testing import CountryTestBase


class Rwanda(CountryTestBase):
    location: str = "Rwanda"
    units: str = "samples tested"
    source_label: str = "Rwanda Ministry of Health"
    source_url: str = "https://gis.rbc.gov.rw/server/rest/services/Hosted/service_b580a3db9319449e82045881f1667b01/FeatureServer/0/query"
    source_url_ref: str = "https://rbc.gov.rw/index.php?id=707"
    rename_columns: dict = {
        # "attributes.sample_tested": "Daily change in cumulative total",
        "attributes.cumulative_test": "Cumulative total",
        "attributes.created_date": "Date",
    }

    date_start: str = "2021-11-08"

    params: dict = {
        "f": "json",
        "where": "1=1",
        "returnGeometry": False,
        "spatialRel": "esriSpatialRelIntersects",
        "orderByFields": "created_date desc",
        "outFields": "*",
        "resultRecordCount": 32000,
        "resultType": "standard",
        "cacheHint": True,
    }

    def read(self) -> pd.DataFrame:
        """Reads data from source."""
        data = request_json(self.source_url, params=self.params)
        df = pd.json_normalize(data, record_path=["features"]).dropna(subset=["attributes.cumulative_test"])
        return df

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans date column"""
        return df.assign(Date=clean_date_series(df["Date"], unit="ms"))

    def pipe_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter data"""
        df = df[df["Cumulative total"] != 5147843.0]
        df = df[(df["Date"] >= self.date_start)]
        return df.drop_duplicates(subset="Date")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """pipeline for data"""
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_date)
            .pipe(self.pipe_filter)
            .pipe(self.pipe_metadata)
            .pipe(make_monotonic)
            .sort_values("Date")
            .drop_duplicates(subset=["Cumulative total"], keep="first")
        )

    def export(self):
        """Exports data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, attach=True)


def main():
    Rwanda().export()
