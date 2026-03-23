import re

from bs4 import BeautifulSoup
import pandas as pd

from cowidev.utils.web import get_soup
from cowidev.utils.clean import clean_count, extract_clean_date
from cowidev.testing.utils.incremental import increment


class Vietnam:
    location = "Vietnam"
    units = "people tested"
    source_label = "Ministry of Health of Vietnam"
    # base_url = "https://suckhoedoisong.vn"
    base_url = "https://covid19.gov.vn"
    source_url = "https://covid19.gov.vn/ban-tin-covid-19.htm"
    regex = {
        "title": r"Ngày",
        "date": r"(\d{2}\-\d{2}\-\d{4})",
        "count": r"mẫu tương đương (\d+)",
    }

    def read(self) -> pd.Series:
        """Read data from source."""
        soup = get_soup(self.source_url)
        data = self._parse_data(soup)
        return data

    def _parse_data(self, soup: BeautifulSoup) -> dict:
        """Get data from the source page."""
        # Get relevant link
        url = self._get_relevant_link(soup)
        # Extract text from url
        text = self._get_text_from_url(url)
        # Extract date from text
        soup = get_soup(url)
        date = self._parse_date_from_text(soup)
        # Extract metrics from text
        count = self._parse_metrics(text)
        record = {
            "source_url": url,
            "date": date,
            "count": count,
        }
        return record

    def _get_relevant_link(self, soup: BeautifulSoup) -> str:
        """Get the relevant URL from the source page."""
        elem_list = soup.find_all("a", title=re.compile(self.regex["title"]))
        if not elem_list:
            raise ValueError("No relevant links found, please update the regex")
        href = elem_list[0]["href"]
        url = f"{self.base_url}{href}"
        return url

    def _get_text_from_url(self, url: str) -> str:
        """Extract text from URL."""
        soup = get_soup(url)
        text = soup.get_text()
        text = re.sub(r"(\d)\.(\d)", r"\1\2", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def _parse_date_from_text(self, soup) -> str:
        """Get date from text."""
        date_raw = soup.select(".detail-time div")[0].text
        return extract_clean_date(date_raw, r"(\d{2}\/\d{2}\/\d{4})", "%d/%m/%Y")

    def _parse_metrics(self, text: str) -> int:
        """Get metrics from text."""
        count = re.search(self.regex["count"], text).group(1)
        return clean_count(count)

    def export(self):
        """Export data to CSV."""
        data = self.read()
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
    Vietnam().export()
