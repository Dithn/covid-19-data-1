import re

from bs4 import BeautifulSoup, element
import pandas as pd

from cowidev.utils.web import get_soup
from cowidev.utils.clean import clean_count, clean_date
from cowidev.testing.utils.incremental import increment


class Fiji:
    location = "Fiji"
    units = "tests performed"
    source_label = "Fiji Ministry of Health & Medical Services"
    notes = ""
    source_url = "https://www.health.gov.fj/page/"
    _num_max_pages = 3
    _num_rows_per_page = 3
    __element = None
    regex = {
        "title": r"COVID-19 Update",
        "year": r"\d{4}",
        "date": r"tests have been reported for (\w+ \d+)",
        "count": r"tests since 2020 are (\d+,\d+)",
    }

    def read(self) -> pd.Series:
        """Read data from source."""
        data = []

        for cnt in range(1, self._num_max_pages + 1):
            url = f"{self.source_url}{cnt}/"
            soup = get_soup(url)
            for _ in range(self._num_rows_per_page):
                data, proceed = self._parse_data(soup)
                if not proceed:
                    return pd.Series(data)
        return None

    def _parse_data(self, soup: BeautifulSoup) -> tuple:
        """Get data from the source page."""
        # Get relevant element list
        self._get_list_of_elements(soup)
        if not self.__element:
            return None, True
        # Get relevant element and year from element list
        elem, year = self._get_relevant_element_and_year()
        # Extract url and date from element
        url = self._parse_link_from_element(elem)
        # Extract text from url
        text = self._get_text_from_url(url)
        # Extract metrics from text
        date = self._parse_date_from_text(year, text)
        if not date:
            return None, True
        # Extract metrics from text
        count = self._parse_metrics(text)
        record = {
            "source_url": url,
            "date": date,
            "count": count,
        }
        return record, False

    def _get_list_of_elements(self, soup: BeautifulSoup) -> None:
        """Get the relevant elements list from the source page."""
        elem_list = soup.find_all("h2")
        self.__element = [title for title in elem_list if self.regex["title"] in title.text]

    def _get_relevant_element_and_year(self) -> tuple:
        """Get the relevant element and year from the element list."""
        elem = self.__element.pop(0)
        year = re.search(self.regex["year"], elem.text).group()
        return elem, year

    def _parse_date_from_text(self, year: str, text: str) -> str:
        """Get date from relevant element."""
        match = re.search(self.regex["date"], text)
        if not match:
            return None
        month_day = match.group(1)
        return clean_date(f"{month_day} {year}", "%B %d %Y")

    def _parse_link_from_element(self, elem: element.Tag) -> str:
        """Get link from relevant element."""
        link = elem.find("a")["href"]
        return link

    def _get_text_from_url(self, url: str) -> str:
        """Extract text from the url."""
        soup = get_soup(url)
        text = soup.get_text().replace("\n", " ").replace("\xa0", "").lower()
        return text

    def _parse_metrics(self, text: str) -> int:
        """Get metrics from news text."""
        match = re.search(self.regex["count"], text)
        if not match:
            raise TypeError(("Website Structure Changed, please update the script"))
        count = match.group(1)
        return clean_count(count)

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
    Fiji().export()
