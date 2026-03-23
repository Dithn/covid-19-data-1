import pandas as pd

from cowidev.testing import CountryTestBase


class Malaysia(CountryTestBase):
    location: str = "Malaysia"
    units: str = "people tested"
    source_label: str = "Malaysia Ministry of Health"
    source_url: str = "https://raw.githubusercontent.com/MoH-Malaysia/covid19-public/main/epidemic/tests_malaysia.csv"
    source_url_ref: str = "https://github.com/MoH-Malaysia/covid19-public"
    notes: str = "Made available by the Malaysia Ministry of Health on GitHub"
    rename_columns: dict = {"date": "Date"}

    def read(self) -> pd.DataFrame:
        return pd.read_csv(self.source_url)

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.sort_values("Date")
        daily = df["rtk-ag"] + df["pcr"]
        return df.assign(**{"Daily change in cumulative total": daily, "Cumulative total": daily.cumsum()}).drop(
            columns=["rtk-ag", "pcr"]
        )

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_rename_columns).pipe(self.pipe_metrics).pipe(self.pipe_metadata)

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Malaysia().export()
