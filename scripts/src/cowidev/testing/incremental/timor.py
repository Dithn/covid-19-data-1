import re

from bs4 import BeautifulSoup, element
import pandas as pd

from cowidev.utils import get_soup, clean_count, clean_date
from cowidev.testing import CountryTestBase


class TimorLeste(CountryTestBase):
    location: str = "Timor"
    units: str = "tests performed"
    source_label: str = "Ministry of Health"
    source_url: str = "https://covid19.gov.tl/dashboard/"
    source_url_ref: str = "https://covid19.gov.tl/dashboard/"
    regex: dict = {
        "date": r"(\w+ \d{1,2}, \d{4})",
        "element": r"Komulativo Teste",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        soup = get_soup(self.source_url)
        df = self._parse_data(soup)
        return df

    def _parse_data(self, soup: BeautifulSoup) -> pd.DataFrame:
        """Parse data from soup"""
        # Get the element
        elem = soup.find(text=re.compile(self.regex["element"]))
        if not elem:
            raise ValueError("Element not found, please update the script")
        # Get the metrics
        count = self._parse_metrics(elem)
        # Get the date from soup
        date = self._parse_date(soup)
        df = pd.DataFrame(
            {
                "Date": [date],
                "Cumulative total": [count],
            }
        )
        return df

    def _parse_metrics(self, elem: element.Tag) -> int:
        """Parse metrics from element"""
        text = elem.find_next_sibling().text
        count = re.sub(r"\D", "", text)
        return clean_count(count)

    def _parse_date(self, soup: BeautifulSoup) -> str:
        """Parse date from soup"""
        text = re.sub(r"\s+", " ", soup.text)
        date = re.search(r"(\w+ \d{1,2}, \d{4})", text).group(1).lower()
        return clean_date(date, "%B %d, %Y")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data processing"""
        return (
            df.pipe(self.pipe_metadata)
            .pipe(self.pipe_merge_current)
            .drop_duplicates(subset=["Cumulative total"], keep="first")
        )

    def export(self):
        """Export data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    TimorLeste().export()
