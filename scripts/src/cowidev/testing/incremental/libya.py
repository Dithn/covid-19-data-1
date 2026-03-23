import re

from bs4 import BeautifulSoup, element
import pandas as pd

from cowidev.utils.web import get_soup
from cowidev.utils.clean import clean_count, clean_date
from cowidev.testing.utils.incremental import increment


class Libya:
    location = "Libya"
    units = "samples tested"
    source_label = "Libya National Centre for Disease Control"
    notes = ""
    source_url = "https://ncdc.org.ly/Ar"
    regex = {
        "samples": r"عدد العينات",
        "date": r"(\d+ \/ \d+ \/ \d+.)",
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
        # Extract date from soup
        date = self._parse_date_from_soup(soup)
        # Extract metrics from element
        daily_change = self._parse_metrics(elem)

        record = {
            "source_url": self.source_url,
            "date": date,
            "daily_change": daily_change,
        }
        return record

    def _get_relevant_element(self, soup: BeautifulSoup) -> element.Tag:
        """Get the relevant element in soup."""
        elem = soup.find(text=self.regex["samples"]).find_parent(class_="wptb-text-container").find_next_sibling()
        return elem

    def _parse_date_from_soup(self, soup: BeautifulSoup) -> str:
        """Get date from soup."""
        date_list = soup.find_all("strong")
        date = [date for date in date_list if re.search(self.regex["date"], date.text)]
        date = date[0].text.replace(" ", "").replace("حتىتاريخ", "").replace("م", "")
        return clean_date(date, "%d/%m/%Y")

    def _parse_metrics(self, elem: element.Tag) -> int:
        """Get metrics from element."""
        count = elem.text.replace(",", "")
        return clean_count(count)

    def export(self):
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
    Libya().export()
