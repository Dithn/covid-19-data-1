from tableauscraper import TableauScraper
import pandas as pd

from cowidev.utils import clean_date, clean_count
from cowidev.testing import CountryTestBase


class Paraguay(CountryTestBase):
    location: str = "Paraguay"
    units: str = "tests performed"
    source_label: str = "Ministry of Public Health and Social Welfare"
    source_url: str = "https://public.tableau.com/views/COVID-19PYTableauPublic/COVID-19Prensa"
    source_url_ref: str = "https://www.mspbs.gov.py/reporte-covid19.html"

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        df = self._parse_data(self.source_url)
        return df

    def _parse_data(self, url: str) -> pd.DataFrame:
        """Parse data from url"""
        t_scraper = TableauScraper()
        t_scraper.loads(url)
        # Get the metrics
        count = self._parse_metrics(t_scraper)
        # Get the date
        date = self._parse_date(t_scraper)
        df = pd.DataFrame(
            {
                "Date": [date],
                "Cumulative total": [count],
            }
        )
        return df

    def _parse_metrics(self, t_scraper: TableauScraper) -> int:
        """Parse metrics from TableauScraper"""
        count = int(t_scraper.getWorksheet("Resumen").data.loc[0, "SUM(Cantidad Pruebas)-alias"])
        return clean_count(count)

    def _parse_date(self, t_scraper: TableauScraper) -> str:
        """Parse date from TableauScraper"""
        date = t_scraper.getWorksheet("COVID-19 | Prensa.Titulo").data.iat[0, 0]
        return clean_date(date, "%d/%m/%Y")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data processing"""
        return df.pipe(self.pipe_metadata)

    def export(self):
        """Export data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, attach=True)


def main():
    Paraguay().export()
