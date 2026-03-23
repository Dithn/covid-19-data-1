import re

from bs4 import BeautifulSoup, element
import pandas as pd

from cowidev.utils import get_soup, clean_count, clean_date
from cowidev.testing import CountryTestBase


class Belize(CountryTestBase):
    location: str = "Belize"
    units: str = "tests performed"
    source_label: str = "Ministry of Health and Wellness"
    source_url: str = "https://sib.org.bz/covid-19/by-the-numbers/"
    source_url_ref: str = "https://sib.org.bz/covid-19/by-the-numbers/"
    regex: dict = {
        "element": r"Tests Completed",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        soup = get_soup(self.source_url)
        df = self._parse_data(soup)
        return df

    def _parse_data(self, soup: BeautifulSoup) -> pd.DataFrame:
        """Parse data from soup"""
        # Get the element
        elem = soup.find(text=self.regex["element"]).parent.parent.parent.previous_sibling
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
        count = clean_count(elem.find(class_="stats-number")["data-counter-value"])
        return count

    def _parse_date(self, soup: BeautifulSoup) -> str:
        """Parse date from soup"""
        date = soup.find("em").text.lower()
        date = re.sub(r"(\d{1,2})(\w+),", r"\1", date)
        return clean_date(date, "last updated: %B %d %Y.")

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
    Belize().export()
