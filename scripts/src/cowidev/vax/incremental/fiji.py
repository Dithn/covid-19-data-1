import re

from bs4 import BeautifulSoup, element
import pandas as pd

from cowidev.utils import get_soup, clean_count, clean_date
from cowidev.vax.utils.base import CountryVaxBase


class Fiji(CountryVaxBase):
    location: str = "Fiji"
    source_url: str = "https://www.health.gov.fj/page/"
    source_url_ref: str = ""
    _num_max_pages: int = 3
    _num_rows_per_page: int = 3
    __element = None
    regex = {
        "title": r"COVID-19 Update",
        "year": r"\d{4}",
        "date": r"tests have been reported for (\w+ \d+)",
        "booster": r"(\d+) individuals have so far received booster doses.",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source."""
        data = []
        for cnt in range(1, self._num_max_pages + 1):
            url = f"{self.source_url}{cnt}/"
            soup = get_soup(url)
            for _ in range(self._num_rows_per_page):
                data, proceed = self._parse_data(soup)
                if not proceed:
                    return pd.DataFrame(data)
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
        self.source_url_ref = self._parse_link_from_element(elem)
        # Extract text from url
        text = self._get_text_from_url(self.source_url_ref)
        # Extract metrics from text
        date = self._parse_date_from_text(year, text)
        if not date:
            return None, True
        # Extract metrics from text
        booster = self._parse_metrics(text)
        record = {
            "date": [date],
            "total_boosters": [booster],
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
        text = re.sub(r"(\d),(\d)", r"\1\2", text)
        return text

    def _parse_metrics(self, text: str) -> int:
        """Get metrics from news text."""
        match = re.search(self.regex["booster"], text)
        if not match:
            raise TypeError(("Website Structure Changed, please update the script"))
        count = match.group(1)
        return clean_count(count)

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes vaccine names."""
        return df.assign(vaccine="Moderna, Oxford/AstraZeneca, Pfizer/BioNTech")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data."""
        return df.pipe(self.pipe_metadata).pipe(self.pipe_vaccine)

    def export(self):
        """Exports data to csv."""
        data = self.read().pipe(self.pipeline)
        self.export_datafile(data, attach=True)


def main():
    pass


def check_booster():
    Fiji().export()
