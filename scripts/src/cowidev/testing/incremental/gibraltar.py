import re

from bs4 import BeautifulSoup
import pandas as pd

from cowidev.utils import get_soup, clean_count, clean_date
from cowidev.testing import CountryTestBase


class Gibraltar(CountryTestBase):
    location: str = "Gibraltar"
    units: str = "tests performed"
    source_label: str = "The Department of Public Health"
    source_url: str = "https://healthygibraltar.org/news/update-on-wuhan-coronavirus/"
    source_url_ref: str = "https://healthygibraltar.org/news/update-on-wuhan-coronavirus/"
    regex: dict = {
        "date": r"valid as of (\d{1,2})\w+ (\w+ 20\d{2})",
        "count": r"Results received: ([\d,]+)",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        soup = get_soup(self.source_url)
        df = self._parse_data(soup)
        return df

    def _parse_data(self, soup: BeautifulSoup) -> pd.DataFrame:
        """Parse data from soup"""
        # Extract text from soup
        text = soup.get_text().replace("\xa0","")
        # Get the metrics
        count = self._parse_metrics(text)
        # Get the date
        date = self._parse_date(text)
        df = pd.DataFrame(
            {
                "Date": [date],
                "Cumulative total": [count],
            }
        )
        return df

    def _parse_metrics(self, text: str) -> int:
        """Parse metrics from text"""
        count = re.search(self.regex["count"], text).group(1)
        return clean_count(count)

    def _parse_date(self, text: str) -> str:
        """Parse date from text"""
        day,month_year = re.search(self.regex["date"], text.lower()).group(1,2)
        date = f"{day} {month_year}"
        return clean_date(date, "%d %B %Y")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data processing"""
        return df.pipe(self.pipe_metadata)

    def export(self):
        """Export data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, attach=True)


def main():
    Gibraltar().export()
