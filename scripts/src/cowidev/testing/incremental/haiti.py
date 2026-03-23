import re
import tempfile

from bs4 import BeautifulSoup
import pandas as pd
from pdfminer.high_level import extract_text

from cowidev.utils import get_soup, clean_count
from cowidev.utils.clean import extract_clean_date
from cowidev.utils.utils import download_file_from_url
from cowidev.testing.utils.base import CountryTestBase


class Haiti(CountryTestBase):
    location: str = "Haiti"
    units: str = "tests performed"
    source_url: dict = "https://www.mspp.gouv.ht/documentation/"
    source_url_ref: str = None
    source_label: str = "Ministry of Public Health and Population"
    regex: dict = {
        "title": r"surveillance du nouveau Coronavirus \(COVID-19\)",
        "date": r"(\d{1,2}\-\d{1,2}\-20\d{2})",
        "metrics": r"INDICATEURS ([\d,]+)",
    }

    def read(self) -> pd.DataFrame:
        """Reads data from source."""
        soup = get_soup(self.source_url)
        df = self._parse_data(soup)
        return df

    def _parse_data(self, soup: BeautifulSoup) -> pd.DataFrame:
        """Parses data from soup."""
        # Obtain pdf url
        self.source_url_ref = soup.find(
            text=re.compile("surveillance du nouveau Coronavirus \(COVID-19\)")
        ).parent.findNext("a")["href"]
        # Extract text from pdf url
        text = self._extract_text_from_url()
        # Clean data
        df = self._parse_metrics(text)
        return df

    def _extract_text_from_url(self) -> str:
        """Extracts text from pdf."""
        with tempfile.NamedTemporaryFile() as tmp:
            download_file_from_url(self.source_url_ref, tmp.name)
            with open(tmp.name, "rb") as f:
                text = extract_text(f).replace("\n", " ")
        text = re.sub(r"\s+", " ", text)
        return text

    def _parse_metrics(self, text: str) -> pd.DataFrame:
        """Parses metrics from data."""
        # Extract data
        match_count = re.search(self.regex["metrics"], text)
        if not match_count:
            raise ValueError("Unable to extract data from text, please update the regex.")
        count = clean_count(match_count.group(1))
        # Create dataframe
        df = {
            "Cumulative total": [count],
        }
        return pd.DataFrame(df)

    def _parse_date(self, link: str) -> str:
        """Gets date from link."""
        return extract_clean_date(link, self.regex["date"], "%d-%m-%Y")

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes date."""
        return df.assign(Date=self._parse_date(self.source_url_ref))

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data."""
        return df.pipe(self.pipe_date).pipe(self.pipe_metadata)

    def export(self):
        """Exports data to CSV."""
        df = self.read().pipe(self.pipeline)
        # Export to CSV
        self.export_datafile(df, attach=True)


def main():
    Haiti().export()
