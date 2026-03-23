import re
import tempfile
from cowidev.utils.web.scraping import get_soup
import pandas as pd
from bs4 import BeautifulSoup


from pdfminer.high_level import extract_text
from cowidev.utils.web.download import download_file_from_url
from cowidev.utils.clean import clean_date, clean_count

from cowidev.testing.utils.incremental import increment
from cowidev.testing import CountryTestBase


class Palau(CountryTestBase):
    location: str = "Palau"
    units: str = "tests performed"
    source_label: str = "Ministry of Health and Human Services"
    source_url: str = "http://www.palauhealth.org/"
    source_url_ref: str = ""
    regex: dict = {"date": r"(\d{1,2} \w+ 20\d{2})", "count": r"((\d+),(\d+))COVID-19 Testsconducted \(since"}

    def read(self) -> pd.Series:
        data = []
        soup = get_soup(self.source_url)
        data = self._parse_data(soup)

        return pd.Series(data)

    def _parse_data(self, soup: BeautifulSoup) -> tuple:
        """Gets pdf url"""
        sd = soup.find("a", id="HyperLink21")["href"]
        pdf_url = f"{self.source_url}/{sd}"

        """Parses pdf text"""
        with tempfile.NamedTemporaryFile() as tmp:
            download_file_from_url(pdf_url, tmp.name)
            with open(tmp.name, "rb") as f:
                text = extract_text(f)
        text = text.replace("\n", "")

        """Gets metrics from report text"""
        count, date = self._parse_metrics(text)

        record = {
            "count": count,
            "date": date,
        }

        return record, False

    def _parse_metrics(self, text: str) -> tuple:
        """Get metrics from report text."""
        count = clean_count(re.search(self.regex["count"], text).group(1))
        date = clean_date(re.search(self.regex["date"], text).group(1), "%d %B %Y")

        return count, date

    def export(self):
        data = self.read()[0]
        increment(
            count=data["count"],
            sheet_name=self.location,
            country=self.location,
            units=self.units,
            date=data["date"],
            source_url=self.source_url,
            source_label=self.source_label,
        )


def main():
    Palau().export()
