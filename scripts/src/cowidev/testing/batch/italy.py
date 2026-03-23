import pandas as pd
from cowidev.utils.clean import clean_date_series

from cowidev.testing import CountryTestBase
from cowidev.testing.utils import make_monotonic


class Italy(CountryTestBase):
    location = "Italy"
    units = "tests performed"
    source_label = "Presidency of the Council of Ministers"
    source_url = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale.csv"
    source_url_ref = "https://github.com/pcm-dpc/COVID-19/tree/master/dati-andamento-nazionale/"
    notes = "Made available by the Department of Civil Protection on GitHub"
    rename_columns = {"data": "Date", "tamponi": "Cumulative total"}

    def read(self) -> pd.DataFrame:
        df = pd.read_csv(self.source_url, usecols=["data", "tamponi"])
        df["data"] = df["data"].str.replace("T", " ")
        df["data"] = clean_date_series(df["data"], "%Y-%m-%d %H:%M:%S")
        return df

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.sort_values("Date")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_rename_columns).pipe(self.pipe_metrics).pipe(self.pipe_metadata).pipe(make_monotonic)

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Italy().export()
