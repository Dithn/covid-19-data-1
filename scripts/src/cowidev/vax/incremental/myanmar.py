import re

from bs4 import BeautifulSoup, element
import pandas as pd

from cowidev.utils.web import get_soup
from cowidev.utils.clean import clean_count, clean_date
from cowidev.vax.utils.incremental import increment, enrich_data


class Myanmar:
    location = "Myanmar"
    _base_url = "https://mohs.gov.mm"
    _url_subdirectory = "/main/content/new/list?pagesize=9&pagenumber="
    _num_max_pages = 3
    regex = {
        "title": r"ကိုဗစ်-19 ရောဂါ ကာကွယ်ဆေး ထိုးနှံပြီးစီးမှု",
        "date": r"(\d{1,2}\-\d{1,2}\-20\d{2})",
        "people_vaccinated": r"(\d+) \(Cumulative vaccinated people\)",
        "people_fully_vaccinated": r"(\d+) \(Cumulative fully vaccinated people\)",
        "total_vaccinations": r"(\d+) \(Cumulative vaccinated doses\)",
    }

    def read(self) -> pd.Series:
        """Reads data from source."""
        data = []

        for cnt in range(1, self._num_max_pages + 1):
            url = f"{self._base_url}{self._url_subdirectory}{cnt}"
            soup = get_soup(url, verify=False)
            data, proceed = self._parse_data(soup)
            if not proceed:
                break

        return pd.Series(data)

    def _parse_data(self, soup: BeautifulSoup) -> tuple:
        """Get data from the source page."""
        # Get relevant element
        elem = self._get_relevant_element(soup)
        if not elem:
            return None, True
        # Extract url and date from element
        url, date = self._get_link_and_date_from_element(elem)
        # Extract text from url
        text = self._get_text_from_url(url)

        record = {
            "source_url": url,
            "date": date,
            **self._parse_metrics(text),
        }
        return record, False

    def _get_relevant_element(self, soup: BeautifulSoup) -> element.NavigableString:
        """Gets the relevant element in news feed."""
        elem = soup.find(text=re.compile(self.regex["title"]))
        return elem

    def _get_text_from_url(self, url: str) -> str:
        """Extracts text from the url."""
        soup = get_soup(url, verify=False)
        text = soup.text.replace(",", "")
        text = re.sub(r"\s+", " ", text)
        return text

    def _get_link_and_date_from_element(self, elem: element.NavigableString) -> tuple:
        """Extracts link and date from relevant element."""
        link = self._parse_link_from_element(elem)
        date = self._parse_date_from_element(elem)
        return link, date

    def _parse_date_from_element(self, elem: element.NavigableString) -> str:
        """Gets date from relevant element."""
        date = re.search(self.regex["date"], elem).group(1)
        return clean_date(date, "%d-%m-%Y")

    def _parse_link_from_element(self, elem: element.NavigableString) -> str:
        """Gets link from relevant element."""
        href = elem.findParent("a")["href"]
        url = f"{self._base_url}{href}"
        return url

    def _parse_metrics(self, text: str) -> dict:
        """Gets metrics from news text."""
        people_vaccinated = re.search(self.regex["people_vaccinated"], text).group(1)
        people_fully_vaccinated = re.search(self.regex["people_fully_vaccinated"], text).group(1)
        total_vaccinations = re.search(self.regex["total_vaccinations"], text).group(1)
        return {
            "people_vaccinated": clean_count(people_vaccinated),
            "people_fully_vaccinated": clean_count(people_fully_vaccinated),
            "total_vaccinations": clean_count(total_vaccinations),
        }

    def pipe_location(self, data_series: pd.Series) -> pd.Series:
        """Pipes location."""
        return enrich_data(data_series, "location", self.location)

    def pipe_vaccine(self, data_series: pd.Series) -> pd.Series:
        """Pipes vaccine names."""
        return enrich_data(data_series, "vaccine", "Oxford/AstraZeneca, Sinopharm/Beijing")

    def pipeline(self, data_series: pd.Series) -> pd.Series:
        """Pipeline for data."""
        return data_series.pipe(self.pipe_location).pipe(self.pipe_vaccine)

    def export(self):
        """Exports data to csv."""
        data = self.read().pipe(self.pipeline)
        increment(
            location=data["location"],
            total_vaccinations=data["total_vaccinations"],
            people_vaccinated=data["people_vaccinated"],
            people_fully_vaccinated=data["people_fully_vaccinated"],
            date=data["date"],
            source_url=data["source_url"],
            vaccine=data["vaccine"],
        )


def main():
    Myanmar().export()
