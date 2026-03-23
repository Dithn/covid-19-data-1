import pandas as pd
from cowidev.testing import CountryTestBase


class Peru(CountryTestBase):
    location: str = "Peru"
    units: str = "tests performed"
    source_label: str = "National Institute of Health"
    notes: str = "Ministerio de Salud via https://github.com/jmcastagnetto/covid-19-peru-data"
    source_url: str = (
        "https://raw.githubusercontent.com/jmcastagnetto/covid-19-peru-data/main/datos/covid-19-peru-data.csv"
    )
    source_url_ref: str = (
        "https://datos.ins.gob.pe/dataset/dataset-de-pruebas-moleculares-del-instituto-nacional-de-salud-ins"
    )
    rename_columns: dict = {"date": "Date", "confirmed": "positive", "total_tests": "Cumulative total"}

    # To avoid removing previous data obtained from source_url_ref
    date_start: str = "2020-04-08"

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        df = pd.read_csv(self.source_url)
        return df

    def pipe_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter data"""
        df = df[(df["region"].isna()) & (df["Date"] >= self.date_start)]
        # corrections
        df = df[df["Date"] != "2021-05-31"]
        df = df[df["Date"] != "2021-11-16"]
        return df

    def pipe_pr(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate positive rate"""
        df = df.sort_values("Date")
        cases_over_period = df["positive"].diff().rolling(7).sum()
        tests_over_period = df["Cumulative total"].diff().rolling(7).sum()
        return df.assign(**{"Positive rate": (cases_over_period / tests_over_period).round(3)}).fillna(0)

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data"""
        return df.pipe(self.pipe_rename_columns).pipe(self.pipe_filter).pipe(self.pipe_pr).pipe(self.pipe_metadata)

    def export(self):
        """Export data to CSV"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, attach=True)


def main():
    Peru().export()
