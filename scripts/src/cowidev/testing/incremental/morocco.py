import re

from bs4 import BeautifulSoup
import pandas as pd

from cowidev.utils import get_soup, clean_count
from cowidev.utils.clean import extract_clean_date
from cowidev.testing import CountryTestBase


class Morocco(CountryTestBase):
    location: str = "Morocco"
    units: str = "people tested"
    source_label: str = "Ministry of Health"
    source_url: str = "http://www.covidmaroc.ma/Pages/AccueilAR.aspx"
    source_url_ref: str = "http://www.covidmaroc.ma/Pages/AccueilAR.aspx"
    regex: dict = {
        "date": r"00 (\d{1,2}\-\d{2}\-20\d{2})",
        "count": r"\s+",
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
        text = soup.find("table").find_all("span")[1].text
        count = re.sub(self.regex["count"], "", text)
        return clean_count(count)

    def _parse_date(self, soup: BeautifulSoup) -> str:
        """Parse date from soup"""
        date_str = soup.find("table").find("span").text.replace("\u200b", "")
        return extract_clean_date(date_str, self.regex["date"], "%d-%m-%Y")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data processing"""
        return df.pipe(self.pipe_metadata)

    def export(self):
        """Export data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, attach=True)


def main():
    Morocco().export()
