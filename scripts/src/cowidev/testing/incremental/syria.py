import re
import tempfile


from bs4 import BeautifulSoup, element
import pandas as pd
from pdfminer.high_level import extract_text

from cowidev.utils import get_soup
from cowidev.utils.web.download import download_file_from_url
from cowidev.utils.clean import extract_clean_date, clean_count
from cowidev.testing.utils.incremental import increment
from cowidev.testing import CountryTestBase


class Syria(CountryTestBase):
    location: str = "Syria"
    units: str = "tests performed"
    source_label: str = "WHO Syrian Arab Republic"
    source_url: str = (
        "https://reliefweb.int/updates?advanced-search=%28C226%29_%28S1275%29_%28DT4642%29_%28T4595%29_%28F10%29"
    )
    regex: dict = {"date": r"(\d{1,2} \w+ 20\d{2})", "count": r"Total Test (\d+) (\d+)"}

    def read(self) -> pd.Series:
        """Read data from source."""
        data = []
        soup = get_soup(self.source_url)
        data = self._parse_data(soup)

        return pd.Series(data)

    def _parse_data(self, soup: BeautifulSoup) -> tuple:
        """Parses data from soup"""
        # Get relevant element
        elem = self._get_relevant_element(soup)
        if not elem:
            return None, True
        # Extract url and date from element
        pdf_url, date = self._get_link_and_date_from_element(elem)
        # Extract text
        text = self._parse_pdf_url(pdf_url)
        # Get metrics from text
        count = self._parse_metrics(text)
        record = {
            "source_url": pdf_url,
            "date": date,
            "count": count,
        }
        return record, False

    def _get_relevant_element(self, soup: BeautifulSoup) -> element.Tag:
        """Parses pdf url from soup"""
        elem = soup.find_all("h4", "title")[0].find("a")
        if not elem:
            raise ValueError("Element not found, please check the source")
        return elem

    def _get_link_and_date_from_element(self, elem: element.Tag) -> tuple:
        """Extract link and date from relevant element."""
        pdf_url = self._parse_link_from_element(elem)
        date = self._parse_date_from_element(elem)
        return pdf_url, date

    def _parse_link_from_element(self, elem: element.Tag) -> str:
        """Get link from relevant element."""
        link = get_soup(elem["href"]).find("a", download=True)["href"]
        return link

    def _parse_date_from_element(self, elem: element.Tag) -> str:
        """Get date from relevant element."""
        return extract_clean_date(elem.text, regex=self.regex["date"], date_format="%d %B %Y")

    def _parse_pdf_url(self, pdf_url: str) -> str:
        """Parses pdf text"""
        with tempfile.NamedTemporaryFile() as tmp:
            download_file_from_url(pdf_url, tmp.name)
            with open(tmp.name, "rb") as f:
                text = extract_text(f)
        text = text.replace("\n", "")
        return text

    def _parse_metrics(self, text: str) -> int:
        """Get metrics from report text."""
        return clean_count(
            int(re.search(self.regex["count"], text).group(1) + re.search(self.regex["count"], text).group(2))
        )

    def export(self):
        """Export data to csv."""
        data = self.read()[0]
        increment(
            sheet_name=self.location,
            country=self.location,
            units=self.units,
            date=data["date"],
            source_url=data["source_url"],
            source_label=self.source_label,
            count=data["count"],
        )


def main():
    Syria().export()
