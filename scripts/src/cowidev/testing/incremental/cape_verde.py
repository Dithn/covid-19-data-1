import re

from bs4 import BeautifulSoup, element
import pandas as pd

from cowidev.utils.web import get_soup
from cowidev.utils.clean import clean_count, extract_clean_date
from cowidev.testing.utils.incremental import increment


class CapeVerde:
    location = "Cape Verde"
    units = "tests performed"
    source_label = "Government of Cape Verde"
    source_url = "https://covid19.cv/category/boletim-epidemiologico/"
    regex = {
        "date": r"(\d+) (?:de )?(\w+) de (20\d+)",
        "count": r"(?:total|totais) (?:de|dos|das) (\d+) (?:resultados|amostras)",
    }

    def read(self) -> pd.Series:
        """Read data from source."""
        soup = get_soup(self.source_url)
        data = self._parse_data(soup)
        return pd.Series(data)

    def _parse_data(self, soup: BeautifulSoup) -> dict:
        """Get data from the source page."""
        # Get relevant element
        elem = self._get_relevant_element(soup)
        # Extract url from element
        url = self._parse_link_from_element(elem)
        # Extract text from url
        text = self._get_text_from_url(url)
        # Extract metrics from text
        daily_change = self._parse_metrics(text)
        # Extract date from text
        date = self._parse_date(text)

        record = {
            "source_url": url,
            "date": date,
            "daily_change": daily_change,
        }
        return record

    def _get_relevant_element(self, soup: BeautifulSoup) -> element.Tag:
        """Get the relevant element from the source page."""
        elem = soup.find("h3", class_="elementor-post__title")
        if not elem:
            raise TypeError("Website Structure Changed, please update the script")
        return elem

    def _parse_date(self, text: str) -> str:
        """Get date from relevant element."""
        return extract_clean_date(text.lower(), self.regex["date"], "%d %B %Y", lang="pt")

    def _parse_link_from_element(self, elem: element.Tag) -> str:
        """Get link from relevant element."""
        link = elem.findChild("a")["href"]
        return link

    def _get_text_from_url(self, url: str) -> str:
        """Extract text from the url."""
        soup = get_soup(url)
        text = soup.find(class_="page-content").get_text(strip=True).replace(",", "")
        return text

    def _parse_metrics(self, text: str) -> int:
        """Get metrics from the text."""
        match = re.search(self.regex["count"], text)
        if not match:
            raise ValueError("Website Structure Changed, please update the script")
        return clean_count(match.group(1))

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
            daily_change=data["daily_change"],
        )


def main():
    CapeVerde().export()
