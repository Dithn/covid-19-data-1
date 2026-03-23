import re
import json

from bs4 import BeautifulSoup, element
import pandas as pd

from cowidev.utils import get_soup, clean_count, clean_date
from cowidev.testing import CountryTestBase

class Tunisia(CountryTestBase):
    location: str = "Tunisia"
    units: str = "people tested"
    source_label: str = "Tunisia Ministry of Health"
    source_url: str = "https://onmne.tn"
    source_url_ref: str = "https://onmne.tn"
    regex: dict = {
        "date": r"Chiffres clés mis à jour le ",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        soup = get_soup(self.source_url)
        df = self._parse_data(soup)
        return df

    def _parse_data(self, soup: BeautifulSoup) -> pd.DataFrame:
        """Parse data from soup"""
        # Get the element
        elem = soup.find("span", class_="vcex-milestone-time")
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
        count = json.loads(elem.attrs["data-options"])["endVal"]
        return clean_count(count)

    def _parse_date(self, soup: BeautifulSoup) -> str:
        """Parse date from soup"""
        text = soup.find(text=re.compile(self.regex["date"]))
        date = re.sub(self.regex["date"], "", text).lower()
        return clean_date(date, "%d %B %Y", lang="fr")

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
    Tunisia().export()
