import re
import tempfile

from bs4 import BeautifulSoup
import pandas as pd
from pdfminer.high_level import extract_text

from cowidev.utils import get_soup
from cowidev.utils.clean import clean_count, extract_clean_date
from cowidev.utils.web.download import download_file_from_url, get_base_url
from cowidev.testing.utils.base import CountryTestBase


class SaintVincentAndTheGrenadines(CountryTestBase):
    location: str = "Saint Vincent and the Grenadines"
    units: str = "tests performed"
    source_url: dict = "http://health.gov.vc/health/index.php/c"
    source_url_ref: str = None
    source_label: str = "Ministry of Health, Wellness and the Environment"
    regex: dict = {
        "title": r"COVID-19 Report",
        "pdf": r"Please click for full details",
        "date": r"(\w+ \d{1,2} 20\d{2})",
        "pcr": r"Total PCR Tests done  ([\d,]+)",
        "ag": r"today  Total Rapid Ag \(.*?\)  [\d,]+  ([\d,]+)",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source."""
        soup = get_soup(self.source_url)
        df = self._parse_data(soup)
        return df

    def _parse_data(self, soup: BeautifulSoup) -> pd.DataFrame:
        """Parse data from soup."""
        # Obtain the relevant link
        link = self._parse_link(soup, self.regex["title"])
        # Get soup from link
        soup = get_soup(link)
        # Extract pdf link from soup
        self.source_url_ref = self._parse_link(soup, self.regex["pdf"])
        # Extract text from pdf url
        text = self._extract_text_from_pdf()
        # Parse metrics
        count = self._parse_metrics(text)
        # Parse date
        date = self._parse_date(text)
        # Create dataframe
        df = {
            "Cumulative total": [count],
            "Date": [date],
        }

        return pd.DataFrame(df)

    def _parse_link(self, soup: BeautifulSoup, regex: str) -> str:
        """Parse link from soup."""
        href = soup.find("a", text=re.compile(regex))["href"]
        if not href:
            raise ValueError("Unable to find link, please update the regex.")
        base_url = get_base_url(self.source_url, "http")
        return f"{base_url}{href}"

    def _extract_text_from_pdf(self) -> str:
        """Extract text from pdf."""
        with tempfile.NamedTemporaryFile() as tmp:
            download_file_from_url(self.source_url_ref, tmp.name)
            with open(tmp.name, "rb") as f:
                text = extract_text(f).replace("\n", " ")
        return text

    def _parse_metrics(self, text: str) -> pd.DataFrame:
        """Parse metrics from data."""
        pcr = re.search(self.regex["pcr"], text)
        ag = re.search(self.regex["ag"], text)

        if not pcr and not ag:
            raise ValueError("Unable to extract data from text, please update the regex.")

        pcr = clean_count(pcr.group(1))
        ag = clean_count(ag.group(1))

        return pcr + ag

    def _parse_date(self, text: str) -> str:
        """Get date from text."""
        return extract_clean_date(text.lower(), self.regex["date"], "%b %d %Y")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data."""
        return df.pipe(self.pipe_metadata)

    def export(self):
        """Export data to CSV."""
        df = self.read().pipe(self.pipeline)
        # Export to CSV
        self.export_datafile(df, attach=True)


def main():
    SaintVincentAndTheGrenadines().export()
