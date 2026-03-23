import pandas as pd

from cowidev.utils.web import request_json
from cowidev.utils.clean import clean_date_series, clean_count
from cowidev.testing import CountryTestBase


class Senegal(CountryTestBase):
    location: str = "Senegal"
    units: str = "tests performed"
    source_label: str = "Ministry for Health and Social Action"
    source_url: str = (
        "https://services7.arcgis.com/Z6qiqUaS6ImjYL5S/arcgis/rest/services/tendance_nationale/FeatureServer/0/query"
    )
    source_url_ref: str = "http://www.sante.gouv.sn/"
    rename_columns: dict = {
        "attributes.Nombre_de_tests_realises": "Daily change in cumulative total",
        "attributes.Date": "Date",
    }
    params: dict = {
        "f": "json",
        "where": "1=1",
        "returnGeometry": False,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "Date,Nombre_de_tests_realises",
        "orderByFields": f"Date asc",
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
        return df.assign(Date=clean_date_series(df["Date"], "%d/%m/%Y"))

    def pipe_metrics(self, df: pd.DataFrame):
        """Pipes metrics"""
        return df.assign(
            **{
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
            .sort_values("Date")
        )

    def export(self):
        """Exports data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, attach=True)


def main():
    Senegal().export()
