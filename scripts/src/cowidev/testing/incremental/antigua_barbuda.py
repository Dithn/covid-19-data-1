from bs4 import BeautifulSoup, element
import pandas as pd

from cowidev.utils import get_soup, clean_count, clean_date
from cowidev.testing import CountryTestBase


class AntiguaBarbuda(CountryTestBase):
    location: str = "Antigua and Barbuda"
    units: str = "tests performed"
    source_label: str = "Ministry of Health"
    source_url: str = "https://covid19.gov.ag"
    source_url_ref: str = "https://covid19.gov.ag"

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        soup = get_soup(self.source_url)
        df = self._parse_data(soup)
        return df

    def _parse_data(self, soup: BeautifulSoup) -> pd.DataFrame:
        """Parse data from soup"""
        # Get the element
        elem = soup.find(text="Tests Done").parent
        if not elem:
            raise ValueError("Element not found, please update the script")
        # Get the metrics
        count = self._parse_metrics(elem)
        # Get the date
        date = self._parse_date(elem)
        df = pd.DataFrame(
            {
                "Date": [date],
                "Cumulative total": [count],
            }
        )
        return df

    def _parse_metrics(self, elem: element.Tag) -> int:
        """Parse metrics from element"""
        count = clean_count(elem.find_next_sibling("p", class_="case-Number").text)
        return count

    def _parse_date(self, elem: element.Tag) -> str:
        """Parse date from element"""
        parent_elem = elem.find_parent()
        date_str = parent_elem.find_previous_sibling("h2").text
        return clean_date(date_str, "[Updated on %B %d, %Y]")

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
    AntiguaBarbuda().export()
