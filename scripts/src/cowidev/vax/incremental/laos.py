import re

from bs4 import BeautifulSoup, element
import pandas as pd

from cowidev.utils import clean_count, clean_date, get_soup
from cowidev.vax.utils.incremental import increment, enrich_data


class Laos:
    location = "Laos"
    source_url = "https://www.covid19.gov.la/index.php"
    regex = {
        "dose_1": r"ຮັບວັກຊິນເຂັມທີ 1 (\d+)",
        "dose_2": r"ຮັບວັກຊິນເຂັມທີ 2 (\d+)",
        "date": r"ຂໍ້ມູນ ເວລາ .*? (\d+\/\d+\/\d+)",
    }

    def read(self) -> pd.Series:
        """Reads data from source."""
        soup = get_soup(self.source_url, verify=False)
        data = self._parse_data(soup)
        return pd.Series(data)

    def _parse_data(self, soup: BeautifulSoup) -> dict:
        """Gets data from the source page."""
        # Extract the relevant element
        elem = self._get_relevant_element(soup)
        # Extract the text from the element
        text = self._get_text_from_element(elem)
        # Extract the metrics
        people_vaccinated, people_fully_vaccinated = self._parse_metrics(text)
        total_vaccinations = people_vaccinated + people_fully_vaccinated
        # Extract date
        date = self._parse_date(text)
        record = {
            "date": date,
            "people_vaccinated": people_vaccinated,
            "people_fully_vaccinated": people_fully_vaccinated,
            "total_vaccinations": total_vaccinations,
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

    def _parse_metrics(self, text: str) -> tuple:
        """Gets metrics from the text."""
        dose_1 = re.search(self.regex["dose_1"], text).group(1)
        dose_2 = re.search(self.regex["dose_2"], text).group(1)
        return clean_count(dose_1), clean_count(dose_2)

    def _parse_date(self, text: str) -> str:
        """Gets date from the text."""
        date = re.search(self.regex["date"], text).group(1)
        return clean_date(date, "%d/%m/%Y")

    def pipe_source(self, ds: pd.Series) -> pd.Series:
        """Pipes source url."""
        return enrich_data(ds, "source_url", self.source_url)

    def pipe_location(self, ds: pd.Series) -> pd.Series:
        """Pipes location."""
        return enrich_data(ds, "location", self.location)

    def pipe_vaccine(self, ds: pd.Series) -> pd.Series:
        """Pipes vaccine names."""
        return enrich_data(
            ds,
            "vaccine",
            "Johnson&Johnson, Oxford/AstraZeneca, Pfizer/BioNTech, Sinopharm/Beijing, Sinovac, Sputnik Light, Sputnik V",
        )

    def pipeline(self, ds: pd.Series) -> pd.Series:
        """Pipeline for the data."""
        return ds.pipe(self.pipe_source).pipe(self.pipe_location).pipe(self.pipe_vaccine)

    def export(self):
        """Exports data to csv."""
        data = self.read().pipe(self.pipeline)
        increment(
            location=data["location"],
            date=data["date"],
            vaccine=data["vaccine"],
            source_url=data["source_url"],
            people_vaccinated=data["people_vaccinated"],
            people_fully_vaccinated=data["people_fully_vaccinated"],
            total_vaccinations=data["total_vaccinations"],
        )


def main():
    Laos().export()
