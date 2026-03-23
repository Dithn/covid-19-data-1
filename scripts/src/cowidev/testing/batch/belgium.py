import pandas as pd

from cowidev.testing import CountryTestBase


class Belgium(CountryTestBase):
    location: str = "Belgium"
    source_url: str = "https://epistat.sciensano.be/Data/COVID19BE_tests.csv"
    source_url_ref: str = source_url
    source_label: str = "Sciensano (Belgian institute for health)"
    units: str = "tests performed"
    rename_columns: str = {
        "DATE": "Date",
        "TESTS_ALL": "Daily change in cumulative total",
        "PR": "Positive rate",
    }

    def read(self):
        # Read
        return pd.read_csv(self.source_url, usecols=["DATE", "TESTS_ALL", "TESTS_ALL_POS"])

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.groupby("DATE", as_index=False).sum()
        # Positive rate
        df = df.assign(
            **{"Positive rate": (df.TESTS_ALL_POS.rolling(7).sum() / df.TESTS_ALL.rolling(7).sum()).round(3)}
        )
        # Rename columns
        df = df.pipe(self.pipe_rename_columns)
        # Add columns
        df = df.pipe(self.pipe_metadata)
        return df

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Belgium().export()
