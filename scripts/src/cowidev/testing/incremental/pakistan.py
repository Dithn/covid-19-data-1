from bs4 import BeautifulSoup, element
import pandas as pd

from cowidev.utils.web import get_soup
from cowidev.utils.clean import clean_count, extract_clean_date
from cowidev.testing.utils.incremental import increment


class Pakistan:
    location = "Pakistan"
    units = "tests performed"
    source_label = "Government of Pakistan"
    notes = ""
    source_url = "http://www.covid.gov.pk/"
    regex = {
        "header": "Pakistan statistics ",
        "count": r"Total Tests",
        "date": r"(\d+ \w+, \d+)",
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
        if not elem:
            raise TypeError("Website Structure Changed, please update the script")
        # Extract metrics from relevant element
        count = self._parse_metrics(elem)
        # Extract date from soup
        date = self._parse_date_from_soup(soup)

        record = {
            "source_url": self.source_url,
            "date": date,
            "count": count,
        }
        return record

    def _get_relevant_element(self, soup: BeautifulSoup) -> element.Tag:
        """Get the relevant element from soup."""
        elem = soup.find(text=self.regex["count"]).parent.parent
        return elem

    def _parse_metrics(self, elem: element.Tag) -> int:
        """Get metrics from element."""
        count = elem.span.text
        return clean_count(count)

    def _parse_date_from_soup(self, soup: BeautifulSoup) -> str:
        """Get date from soup."""
        date_text = soup.find(text=self.regex["header"]).parent.findChild(id="last-update")
        return extract_clean_date(date_text.text, self.regex["date"], "%d %b, %Y")

    def export(self):
        """Export data to csv."""
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
    Pakistan().export()
