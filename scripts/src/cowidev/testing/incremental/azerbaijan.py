from bs4 import BeautifulSoup, element
import pandas as pd

from cowidev.utils import get_soup, clean_count
from cowidev.utils.clean.dates import localdate
from cowidev.testing import CountryTestBase


class Azerbaijan(CountryTestBase):
    location: str = "Azerbaijan"
    units: str = "tests performed"
    source_label: str = "Cabinet of Ministers of Azerbaijan"
    source_url: str = "https://koronavirusinfo.az/az/page/statistika/azerbaycanda-cari-veziyyet"
    source_url_ref: str = "https://koronavirusinfo.az/az/page/statistika/azerbaycanda-cari-veziyyet"

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        soup = get_soup(self.source_url, verify=False)
        df = self._parse_data(soup)
        return df

    def _parse_data(self, soup: BeautifulSoup) -> pd.DataFrame:
        """Parse data from soup"""
        # Get the element
        elem = soup.find(text="Müayinə aparılıb").parent
        if not elem:
            raise ValueError("Element not found, please update the script")
        # Get the metrics
        count = self._parse_metrics(elem)
        df = pd.DataFrame(
            {
                "Date": [localdate("Asia/Baku")],
                "Cumulative total": [count],
            }
        )
        return df

    def _parse_metrics(self, elem: element.Tag) -> int:
        """Parse metrics from element"""
        count = clean_count(elem.find_previous_sibling("strong").text)
        return count

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
    Azerbaijan().export()
