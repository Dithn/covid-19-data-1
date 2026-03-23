import re

from bs4 import BeautifulSoup, element
import pandas as pd

from cowidev.utils import clean_count, clean_date, get_soup
from cowidev.testing.utils.incremental import increment


class Laos:
    location = "Laos"
    units = "tests performed"
    source_label = "Ministry of Health"
    notes = ""
    _source_url = "https://www.covid19.gov.la/index.php"
    regex = {
        "tests": r"ຮັບການກວດມື້ນີ້ (\d+)",
        "date": r"ຂໍ້ມູນ ເວລາ .*? (\d+\/\d+\/\d+)",
    }

    def read(self) -> pd.Series:
        """Reads data from source."""
        soup = get_soup(self._source_url)
        data = self._parse_data(soup)
        return pd.Series(data)

    def _parse_data(self, soup: BeautifulSoup) -> dict:
        """Gets data from the source page."""
        # Extract the relevant element
        elem = self._get_relevant_element(soup)
        # Extract the text from the element
        text = self._get_text_from_element(elem)
        # Extract the metrics
        daily_change = self._parse_metrics(text)
        # Extract date
        date = self._parse_date(text)
        record = {
            "source_url": self._source_url,
            "date": date,
            "daily_change": daily_change,
        }
        return record

    def _get_relevant_element(self, soup: BeautifulSoup) -> element.Tag:
        """Gets element from the soup."""
        elem = soup.find("section", {"id": "aa-blog-archive"})
        if not elem:
            raise TypeError("Website Structure Changed, please update the script")
        return elem

    def _get_text_from_element(self, elem: element.Tag) -> str:
        """Gets text from element."""
        return elem.text.replace("\n", " ").replace(",", "")

    def _parse_metrics(self, text: str) -> int:
        """Gets metrics from the text."""
        count = re.search(self.regex["tests"], text).group(1)
        return clean_count(count)

    def _parse_date(self, text: str) -> str:
        """Gets date from the text."""
        date = re.search(self.regex["date"], text).group(1)
        return clean_date(date, "%d/%m/%Y")

    def export(self):
        """Exports data to csv."""
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
    Laos().export()
