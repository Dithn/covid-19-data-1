import pandas as pd

from cowidev.utils.web import request_json
from cowidev.utils.clean import clean_date_series, clean_count

# from cowidev.testing.utils import make_monotonic
from cowidev.testing import CountryTestBase


class UnitedArabEmirates(CountryTestBase):
    location: str = "United Arab Emirates"
    units: str = "tests performed"
    source_label: str = "UAE Federal Competitiveness and Statistics Authority"
    source_url: str = (
        "https://geostat.fcsa.gov.ae/gisserver/rest/services/UAE_COVID19_Statistics_Rates_Layer/FeatureServer/0/query"
    )
    source_url_ref: str = "https://fcsc.gov.ae/en-us/Pages/Covid19/UAE-Covid-19-Updates.aspx"
    rename_columns: dict = {
        "attributes.TESTS": "Daily change in cumulative total",
        # "attributes.CUMULATIVE_TESTS": "Cumulative total",
        "attributes.DATE_": "Date",
    }
    params: dict = {
        "f": "json",
        "where": "1=1",
        "returnGeometry": False,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "DATE_,TESTS",  # ,CUMULATIVE_TESTS
        "orderByFields": "DATE_ asc",
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
                # "Cumulative total": df["Cumulative total"].apply(clean_count),
                "Daily change in cumulative total": df["Daily change in cumulative total"].apply(clean_count),
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
    UnitedArabEmirates().export()
