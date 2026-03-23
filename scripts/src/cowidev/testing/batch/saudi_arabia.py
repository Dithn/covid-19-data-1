import pandas as pd

from cowidev.utils.web import request_json
from cowidev.utils import clean_date_series, clean_count
from cowidev.testing import CountryTestBase

# from cowidev.testing.utils import make_monotonic


class SaudiArabia(CountryTestBase):
    location: str = "Saudi Arabia"
    units: str = "tests performed"
    source_label: str = "Ministry of Health"
    source_url_ref: str = "https://covid19.moh.gov.sa/"
    source_url: str = "https://services6.arcgis.com/bKYAIlQgwHslVRaK/arcgis/rest/services/DailyTestPerformance_ViewLayer/FeatureServer/0/query"
    rename_columns: dict = {
        "attributes.ReportDate": "Date",
        "attributes.DailyTest": "Daily change in cumulative total",
        # "attributes.CumulativeTest": "Cumulative total",
    }
    params: dict = {
        "f": "json",
        "where": "ReportDate>'2020-01-01 00:00:00'",
        "returnGeometry": False,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "ReportDate,DailyTest",  # CumulativeTest,
        "orderByFields": "ReportDate asc",
        "resultOffset": 0,
        "resultRecordCount": 32000,
        "resultType": "standard",
    }

    def read(self) -> pd.DataFrame:
        """Reads data from source."""
        data = request_json(self.source_url, params=self.params)
        df = pd.json_normalize(data, record_path=["features"])
        return df

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans date column"""
        return df.assign(Date=clean_date_series(df["Date"], unit="ms"))

    def pipe_metrics(self, df: pd.DataFrame):
        """Pipes metrics"""
        return df.assign(
            **{
                "Daily change in cumulative total": df["Daily change in cumulative total"].apply(clean_count),
                # "Cumulative total": df["Cumulative total"].apply(clean_count),
            }
        )

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """pipeline for data"""
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_date)
            .pipe(self.pipe_metrics)
            .pipe(self.pipe_metadata)
            # .pipe(make_monotonic)
            .sort_values("Date")
            # .drop_duplicates(subset=["Cumulative total"], keep="first")
        )

    def export(self):
        """Exports data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    SaudiArabia().export()
