import pandas as pd

from cowidev.utils.clean import clean_date_series

from cowidev.testing import CountryTestBase


class Malta(CountryTestBase):
    location = "Malta"
    units = "tests performed"
    source_label = "COVID-19 Public Health Response Team (Ministry for Health)"
    source_url = (
        "https://raw.githubusercontent.com/COVID19-Malta/COVID19-Data/master/COVID-19%20Malta%20-%20COVID%20Tests.csv"
    )
    source_url_ref = "https://github.com/COVID19-Malta/COVID19-Data/"
    notes = pd.NA
    rename_columns = {"Publication date": "Date", "Total NAA and rapid antigen tests": "Cumulative total"}

    def read(self) -> pd.DataFrame:
        df = pd.read_csv(self.source_url, usecols=["Publication date", "Total NAA and rapid antigen tests"])
        df["Publication date"] = clean_date_series(df["Publication date"], "%d/%m/%Y")
        return df

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.sort_values("Date")
        return df

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_rename_columns).pipe(self.pipe_metrics).pipe(self.pipe_metadata)

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Malta().export()
