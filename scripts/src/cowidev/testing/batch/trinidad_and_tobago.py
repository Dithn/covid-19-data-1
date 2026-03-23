import pandas as pd

from cowidev.utils.web import request_json
from cowidev.utils.clean import clean_date_series
from cowidev.testing.utils import make_monotonic
from cowidev.testing import CountryTestBase


class TrinidadAndTobago(CountryTestBase):
    location: str = "Trinidad and Tobago"
    units: str = "people tested"
    source_label: str = "Ministry of Health"
    source_url: str = "https://services3.arcgis.com/x3I4DqUw3b3MfTwQ/arcgis/rest/services/service_7a519502598f492a9094fd0ad503cf80/FeatureServer/0/query?f=json&resultOffset=0&resultRecordCount=32000&where=report_dt%20IS%20NOT%20NULL%20AND%20report_dt%20BETWEEN%20timestamp%20%272020-12-20%2021%3A00%3A00%27%20AND%20CURRENT_TIMESTAMP&orderByFields=report_dt%20asc&outFields=unique_public_private_test,CreationDate,positive_tests&resultType=standard&returnGeometry=false&spatialRel=esriSpatialRelIntersects"
    source_url_ref: str = "https://www.covid19.gov.tt/"
    rename_columns: dict = {
        "attributes.unique_public_private_test": "Cumulative total",
        "attributes.CreationDate": "Date",
        "attributes.positive_tests": "positive",
    }

    def read(self) -> pd.DataFrame:
        """Reads data from source."""
        data = request_json(self.source_url)
        df = pd.json_normalize(data, record_path=["features"]).dropna(subset=["attributes.unique_public_private_test"])
        return df.drop_duplicates(subset="attributes.unique_public_private_test")

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans date column"""
        return df.assign(Date=clean_date_series(df["Date"], unit="ms"))

    def pipe_pr(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Positive Rate"""
        df["Positive rate"] = (
            df.positive.diff().rolling(7).sum().div(df["Cumulative total"].diff().rolling(7).sum()).round(3)
        ).fillna(0)
        df = df[df["Date"] != "2021-03-27"]
        return df.drop_duplicates(subset="Date")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """pipeline for data"""
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_date)
            .pipe(self.pipe_pr)
            .pipe(self.pipe_metadata)
            .pipe(make_monotonic)
            .sort_values("Date")
        )

    def export(self):
        """Exports data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    TrinidadAndTobago().export()
