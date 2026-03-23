import re
from datetime import date

from bs4 import BeautifulSoup, element
import pandas as pd

from cowidev.utils.web import get_soup
from cowidev.utils.clean import clean_count, clean_date
from cowidev.testing.utils.incremental import increment


class Ukraine:
    location = "Ukraine"
    units = "tests performed"
    source_label = "Cabinet of Ministers of Ukraine"
    notes = ""
    source_url = "https://covid19.gov.ua/en"
    regex = {
        "count": r"total of tests",
        "date": r"Information as of (\w+) (\d{1,2})",
    }

    def read(self) -> pd.Series:
        """Read data from source."""
        soup = get_soup(self.source_url)
        data = self._parse_data(soup)
        return pd.Series(data)

    def _parse_data(self, soup: BeautifulSoup) -> tuple:
        """Get data from the source page."""
        # Get relevant element
        elem = self._get_relevant_element(soup)
        # Extract date from soup
        date_ = self._parse_date(soup)
        # parse metrics from element
        count = self._parse_metrics(elem)
        record = {
            "source_url": self.source_url,
            "date": date_,
            "count": count,
        }
        return record

    def _get_relevant_element(self, soup: BeautifulSoup) -> element.Tag:
        """Get the relevant element in news feed."""
        elem = soup.find(text=re.compile(self.regex["count"])).parent.find_next_sibling(class_="field-value")
        if not elem:
            raise TypeError("Website Structure Changed, please update the script")
        return elem

    def _parse_metrics(self, elem: element.Tag) -> int:
        """Gets metrics from the element."""
        count = elem.text.strip().replace(" ", "")
        return clean_count(count)

    def _parse_date(self, soup: BeautifulSoup) -> str:
        """Gets date from the source page."""
        year = date.today().year
        text = soup.find(text=re.compile(self.regex["date"]))
        month, day = re.search(self.regex["date"], text).group(1, 2)
        return clean_date(f"{year} {month} {day}", "%Y %B %d")

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
    Ukraine().export()
