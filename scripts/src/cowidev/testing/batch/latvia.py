import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.utils import clean_date_series


class Latvia(CountryTestBase):
    location = "Latvia"
    units = "tests performed"
    source_label = "Center for Disease Prevention and Control"
    source_url = "https://data.gov.lv/dati/dataset/f01ada0a-2e77-4a82-8ba2-09cf0cf90db3/resource/d499d2f0-b1ea-4ba2-9600-2c701b03bd4a/download/covid_19_izmeklejumi_rezultati.csv"
    source_url_ref = "https://data.gov.lv/dati/eng/dataset/covid-19"
    notes = "Collected from the Latvian Open Data Portal"
    rename_columns = {
        "Datums": "Date",
        "TestuSkaits": "Daily change in cumulative total",
    }

    def read(self) -> pd.DataFrame:
        return pd.read_csv(self.source_url, usecols=["Datums", "TestuSkaits"], sep=";", encoding="latin-1")

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        df["Date"] = clean_date_series(df["Date"], "%Y.%m.%d.")
        # df["Date"] = df["Date"].str.replace(".", "-", regex=True)
        return df

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_rename_columns).pipe(self.pipe_date).pipe(self.pipe_metadata)

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Latvia().export()
