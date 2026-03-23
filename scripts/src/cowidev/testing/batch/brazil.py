import pandas as pd

from cowidev.testing import CountryTestBase


class Brazil(CountryTestBase):
    location: str = "Brazil"
    units: str = "tests performed"
    source_label: str = "Coronavírus Brasil"
    source_url: str = "https://raw.githubusercontent.com/wcota/covid19br/master/cases-brazil-states.csv"
    source_url_ref: str = "https://coronavirusbra1.github.io/"
    notes: str = "Made available by Wesley Cota on GitHub"
    rename_columns: dict = {"date": "Date", "tests": "Cumulative total"}

    def read(self) -> pd.DataFrame:
        return pd.read_csv(self.source_url, usecols=["date", "state", "tests"])

    def pipe_rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns=self.rename_columns)

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.sort_values("Date")
        df = (
            df.drop(df[df.state != "TOTAL"].index)
            .drop(columns="state")
            .dropna()
            .drop_duplicates(subset=["Cumulative total"])
        )
        # remove non-monotonically increasing values between 2021-02-04 and 2021-02-07
        df = df[(df["Date"] < "2021-02-04") | (df["Date"] > "2021-02-07")]
        df["Cumulative total"] = df["Cumulative total"].astype(int)
        return df

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_rename_columns).pipe(self.pipe_metrics).pipe(self.pipe_metadata)

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Brazil().export()
