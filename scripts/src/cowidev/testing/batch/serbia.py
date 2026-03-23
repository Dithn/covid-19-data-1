import pandas as pd

from cowidev.testing import CountryTestBase


class Serbia(CountryTestBase):
    location: str = "Serbia"
    units: str = "people tested"
    source_label: str = "Ministry of Health"
    base_url: str = "https://github.com/aleksandar-jovicic/COVID19-Serbia/{}/master/timeseries.csv"
    notes = "Made available by Aleksandar Jovičić on Github"
    testing_type: str = "PCR only"
    rename_columns: dict = {"ts": "Date", "tested": "Cumulative total"}

    @property
    def source_url(self):
        return self.base_url.format("raw")

    @property
    def source_url_ref(self):
        return self.base_url.format("blob")

    def read(self) -> pd.DataFrame:
        df = pd.read_csv(self.source_url, usecols=["ts", "tested"], parse_dates=["ts"])
        return df

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(Date=df.Date.dt.strftime("%Y-%m-%d"))

    def pipe_cumulative_total(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.groupby("Date", as_index=False).agg({"Cumulative total": max})

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_date)
            .pipe(self.pipe_cumulative_total)
            .pipe(self.pipe_metadata)
        )

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Serbia().export()
