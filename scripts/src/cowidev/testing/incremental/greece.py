import re

from bs4 import BeautifulSoup, element
import pandas as pd

from cowidev.utils import get_soup, clean_count, clean_date
from cowidev.testing import CountryTestBase


class Greece(CountryTestBase):
    location: str = "Greece"
    units: str = "samples tested"
    source_label: str = "National Organization of Public Health"
    source_url: str = "https://covid19.gov.gr/"
    source_url_ref: str = "https://covid19.gov.gr/"
    regex: dict = {
        "date": r"elementor-element-5b9d061",
        "element": r"elementor-element-9df72a6",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        soup = get_soup(self.source_url)
        df = self._parse_data(soup)
        return df

    def _parse_data(self, soup: BeautifulSoup) -> pd.DataFrame:
        """Parse data from soup"""
        # Get the element
        elem = soup.find(class_=self.regex["element"])
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
        count = elem.text
        return clean_count(re.sub(r"\D", "", count))

    def _parse_date(self, soup: BeautifulSoup) -> str:
        """Parse date from soup"""
        date = soup.find(class_=self.regex["date"]).text
        return clean_date(re.sub(r"\D", "", date), "%d%m%Y")

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
    Greece().export()
