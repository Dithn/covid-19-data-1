import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.utils import clean_date_series


class Thailand(CountryTestBase):
    location = "Thailand"
    source_url = "https://data.go.th/dataset/9f6d900f-f648-451f-8df4-89c676fce1c4/resource/0092046c-db85-4608-b519-ce8af099315e/download"
    source_url_ref = "https://data.go.th/dataset/covid-19-testing-data"
    source_label = "Department of Medical Sciences Ministry of Public Health"
    units = "tests performed"
    rename_columns = {"Total Testing": "Daily change in cumulative total"}

    def read(self):
        df = pd.read_csv(self.source_url, usecols=["Date", "Total Testing"])
        return df

    def pipe_date(self, df: pd.DataFrame):
        df = df[~df.Date.isin(["Cannot specify date"])]
        return df.assign(Date=clean_date_series(df.Date, "%d/%m/%Y"))

    def pipe_filter(self, df: pd.DataFrame):
        return df[df["Daily change in cumulative total"] > 0]

    def pipeline(self, df: pd.DataFrame):
        return df.pipe(self.pipe_date).pipe(self.pipe_rename_columns).pipe(self.pipe_filter).pipe(self.pipe_metadata)

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Thailand().export()
