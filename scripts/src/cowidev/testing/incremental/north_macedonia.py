import re

from bs4 import BeautifulSoup
import pandas as pd

from cowidev.utils import get_soup, clean_count, clean_date
from cowidev.testing import CountryTestBase


class NorthMacedonia(CountryTestBase):
    location: str = "North Macedonia"
    units: str = "tests performed"
    source_label: str = "Ministry of Health"
    source_url: str = "https://koronavirus.gov.mk/vesti"
    source_url_ref: str = "https://koronavirus.gov.mk/vesti"
    regex: dict = {
        "date": r"(\d{1,2}.\d{2}.\d{4})",
        "count": r"Досега во земјата се направени вкупно (\d+)",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        soup = get_soup(self.source_url)
        df = self._parse_data(soup)
        return df

    def _parse_data(self, soup: BeautifulSoup) -> pd.DataFrame:
        """Parse data from soup"""
        # Get the article URL
        link = soup.find("article", {"class": "category-izvestuvanja"}).find("a")["href"]
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
        text = re.sub(r"(\d)\.(\d)", r"\1\2", text)
        count = re.search(self.regex["count"], text).group(1)
        return clean_count(count)

    def _parse_date(self, soup: BeautifulSoup) -> str:
        """Parse date from soup"""
        text = soup.get_text()
        date = re.search(self.regex["date"], text).group(1)
        return clean_date(date, "%d.%m.%Y")

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
    NorthMacedonia().export()
