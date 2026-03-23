import re

from bs4 import BeautifulSoup
import pandas as pd

from cowidev.utils import get_soup, clean_count
from cowidev.utils.clean import extract_clean_date
from cowidev.testing import CountryTestBase


class Togo(CountryTestBase):
    location: str = "Togo"
    units: str = "tests performed"
    source_label: str = "Ministry of Health"
    source_url: str = "https://covid19.gouv.tg/"
    source_url_ref: str = "https://covid19.gouv.tg/"
    regex: dict = {
        "date": r"(\d{1,2} \w+ 20\d{2})",
        "count": r"Nombre total ",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        soup = get_soup(self.source_url)
        df = self._parse_data(soup)
        return df

    def _parse_data(self, soup: BeautifulSoup) -> pd.DataFrame:
        """Parse data from soup"""
        # Get the metrics
        count = self._parse_metrics(soup)
        # Get the date
        date = self._parse_date(soup)
        df = pd.DataFrame(
            {
                "Date": [date],
                "Cumulative total": [count],
            }
        )
        return df

    def _parse_metrics(self, soup: BeautifulSoup) -> int:
        """Parse metrics from soup"""
        elem = soup.find(text=re.compile(self.regex["count"]))
        count = elem.parent.parent.parent.parent.text
        return clean_count(count)

    def _parse_date(self, soup: BeautifulSoup) -> str:
        """Parse date from soup"""
        date_str = soup.find("h2", text=re.compile(self.regex["date"])).text
        return extract_clean_date(date_str, self.regex["date"], "%d %B %Y", lang="fr")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data processing"""
        return df.pipe(self.pipe_metadata)

    def export(self):
        """Export data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, attach=True)


def main():
    Togo().export()
