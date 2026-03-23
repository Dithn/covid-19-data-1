from bs4 import element
import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.utils.web import get_soup
from cowidev.utils.clean import clean_date_series


class Luxembourg(CountryTestBase):
    location: str = "Luxembourg"
    units: str = "tests performed"
    source_label: str = "Luxembourg Ministry of Health"
    source_url_ref: str = "https://msan.gouvernement.lu/fr/graphiques-evolution.html"
    rename_columns: dict = {
        "Nombre de tests PCR effectués": "Cumulative total",
        'Nombre de personnes testées "positif"': "positive",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        table = self._get_relevant_table(self.source_url_ref)
        df = pd.read_html(table, header=0)[0].drop_duplicates(["Nombre de tests PCR effectués"])
        return df

    def _get_relevant_table(self, url: str) -> element.Tag:
        """Get the table with the relevant data"""
        soup = get_soup(url)
        tables = soup.find_all("table")
        table = [table for table in tables if table.findChild("caption").text == "Tests COVID-19"][0]
        return str(table)

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert date to datetime"""
        return df.assign(Date=clean_date_series(df["Date"], "%d/%m/%Y"))

    def pipe_pr(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate positive rate"""
        df = df.sort_values("Date")
        cases_over_period = df["positive"].diff().rolling(7).sum()
        tests_over_period = df["Cumulative total"].diff().rolling(7).sum()
        return df.assign(**{"Positive rate": (cases_over_period / tests_over_period).round(3)}).fillna(0)

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data"""
        return df.pipe(self.pipe_rename_columns).pipe(self.pipe_date).pipe(self.pipe_pr).pipe(self.pipe_metadata)

    def export(self):
        """Export data to CSV"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, float_format="%.5f")


def main():
    Luxembourg().export()
