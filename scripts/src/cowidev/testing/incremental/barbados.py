import re

from bs4 import BeautifulSoup
import pandas as pd

from cowidev.utils import get_soup, clean_count, clean_date
from cowidev.testing import CountryTestBase


class Barbados(CountryTestBase):
    location: str = "Barbados"
    units: str = "tests performed"
    source_label: str = "Ministry of Health"
    source_url: str = "https://gisbarbados.gov.bb/top-stories/"
    source_url_ref: str = None
    regex: dict = {
        "title": r"COVID-19 Update",
        "count": r"has conducted (\d+) tests",
    }

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
        self.source_url_ref = link
        soup = get_soup(link)
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
        text = soup.get_text()
        text = re.sub(r"(\d),(\d)", r"\1\2", text)
        count = re.search(self.regex["count"], text).group(1)
        return clean_count(count)

    def _parse_date(self, soup: BeautifulSoup) -> str:
        """Parse date from soup"""
        date_str = soup.find(class_="published").text
        if not date_str:
            raise ValueError("Date not found, please update the script")
        return clean_date(date_str, "%b %d, %Y", minus_days=1)

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data processing"""
        return df.pipe(self.pipe_metadata)

    def export(self):
        """Export data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, attach=True)


def main():
    Barbados().export()
