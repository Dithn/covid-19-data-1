import pandas as pd

from cowidev.testing import CountryTestBase


class Japan(CountryTestBase):
    location = "Japan"
    units = "people tested"
    source_label = "Ministry of Health, Labour and Welfare"
    source_url = "https://www.mhlw.go.jp/content/pcr_tested_daily.csv"
    source_url_ref = source_url
    rename_columns = {"日付": "Date", "PCR 検査実施人数(単日)": "Daily change in cumulative total"}

    def read(self) -> pd.DataFrame:
        return pd.read_csv(self.source_url, usecols=self.rename_columns.keys(), parse_dates=["日付"])

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(Date=df.Date.dt.strftime("%Y-%m-%d"))

    def pipe_filter_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.dropna(subset=["Daily change in cumulative total"])

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_rename_columns).pipe(self.pipe_date).pipe(self.pipe_filter_rows).pipe(self.pipe_metadata)
        )

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Japan().export()
