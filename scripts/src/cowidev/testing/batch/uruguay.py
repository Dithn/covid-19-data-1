import pandas as pd

from cowidev.utils.clean import clean_date_series
from cowidev.utils.web import request_json
from cowidev.testing import CountryTestBase


class Uruguay(CountryTestBase):
    location = "Uruguay"
    units = "people tested"
    source_label = "Ministry of Public Health"
    source_url = "https://estadisticas.msp-uy.com/data.json"
    source_url_ref = source_url
    testing_type = "PCR only"
    rename_columns = {"date": "Date", "total": "Cumulative total"}

    def read(self) -> pd.DataFrame:
        json_dict = request_json(self.source_url)
        return pd.DataFrame.from_dict(json_dict["tests"]["historical"])

    @staticmethod
    def pipe_date(df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(Date=clean_date_series(df.Date, "%Y-%m-%d"))

    @staticmethod
    def pipe_metrics(df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(**{"Cumulative total": df["Cumulative total"].cumsum()})

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_rename_columns).pipe(self.pipe_date).pipe(self.pipe_metrics).pipe(self.pipe_metadata)

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Uruguay().export()
