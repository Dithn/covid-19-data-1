import re

from bs4 import BeautifulSoup
import pandas as pd
import tabula

from cowidev.utils import get_soup, clean_count
from cowidev.utils.clean import extract_clean_date
from cowidev.testing import CountryTestBase


class Vanuatu(CountryTestBase):
    location: str = "Vanuatu"
    units: str = "people tested"
    source_label: str = "Ministry of Health"
    source_url: str = "https://covid19.gov.vu/index.php/surveillance"
    _base_url: str = "https://covid19.gov.vu"
    source_url_ref: str = None
    regex: dict = {
        "title": r"Surveillance Report for Epi Week",
        "date": r"\d{1,2}\/\d{2}\/20\d{2} - (\d{1,2}\/\d{2}\/20\d{2})",
    }

    @property
    def area(Self) -> list:
        """
        Areas of pdf to be extracted
        Returns:
            list: [[y1, x1, y2, x2], ...]
        For more info see: https://github.com/tabulapdf/tabula-java/wiki/Using-the-command-line-tabula-extractor-tool
        """
        return [[122, 188, 140, 419], [437, 7, 484, 299]]

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        soup = get_soup(self.source_url)
        df = self._parse_data(soup)
        return df

    def _parse_data(self, soup: BeautifulSoup) -> pd.DataFrame:
        """Parse data from soup"""
        # Get the article URL
        link = soup.find("a", text=re.compile(self.regex["title"]))["href"]
        if not link:
            raise ValueError("Article not found, please update the script")
        self.source_url_ref = f"{self._base_url}{link}"
        # Parse pdf tables from link
        tables = self._parse_pdf_tables()
        # Get the metrics
        count = self._parse_metrics(tables)
        # Get the date
        date = self._parse_date(tables)
        df = pd.DataFrame(
            {
                "Date": [date],
                "Cumulative total": [count],
            }
        )
        return df

    def _parse_pdf_tables(self) -> list:
        """Parse pdf tables from link"""
        tables = tabula.read_pdf(self.source_url_ref, pages="1", stream=True, area=self.area)
        if len(tables) != 2:
            raise ValueError("PDF structure has changed, please update the script")
        return tables

    def _parse_metrics(self, tables: list) -> int:
        """Parse metrics from the list of tables"""
        count = tables[1].loc[0, "Cumulative"]
        return clean_count(count)

    def _parse_date(self, tables: list) -> str:
        """Parse date from the list of tables"""
        date_str = tables[0].columns[0]
        return extract_clean_date(date_str, self.regex["date"], "%d/%m/%Y")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data processing"""
        return df.pipe(self.pipe_metadata)

    def export(self):
        """Export data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, attach=True) 


def main():
    Vanuatu().export()
