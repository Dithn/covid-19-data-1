import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.testing.utils import make_monotonic
from cowidev.utils import clean_date_series
from cowidev.utils.web.download import read_csv_from_url


class Austria(CountryTestBase):
    location: str = "Austria"
    units: str = "tests performed"
    source_url: str = "https://covid19-dashboard.ages.at/data/CovidFallzahlen.csv"
    source_url_ref: str = "https://www.data.gv.at/katalog/dataset/846448a5-a26e-4297-ac08-ad7040af20f1"
    source_label: str = "Federal Ministry for Social Affairs, Health, Care and Consumer Protection"
    rename_columns: str = {
        "Meldedat": "Date",
        "TestGesamt": "Cumulative total",
    }

    def read(self) -> pd.DataFrame:
        df = read_csv_from_url(
            self.source_url, sep=";", ciphers_low=True, usecols=["Meldedat", "TestGesamt", "Bundesland"]
        )
        df = df[df.Bundesland == "Alle"]
        df = df.groupby("Meldedat", as_index=False)["TestGesamt"].sum()
        return df

    def pipe_date(self, df: pd.DataFrame):
        return df.assign(Date=clean_date_series(df["Date"], "%d.%m.%Y")).sort_values("Date")

    def pipe_filter(self, df: pd.DataFrame):
        df = df.drop_duplicates(subset=["Cumulative total"], keep="first")
        df = df[df["Cumulative total"] != 0]
        return df

    def pipe_exluce_dp(self, df: pd.DataFrame):
        dates = ["2022-01-22"]
        return df[~df.Date.isin(dates)]

    def pipeline(self, df: pd.DataFrame):
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_date)
            .pipe(self.pipe_metadata)
            .pipe(self.pipe_filter)
            .pipe(self.pipe_exluce_dp)
            .pipe(make_monotonic)
        )

    def export(self):
        df = self.read()
        df = df.pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Austria().export()
