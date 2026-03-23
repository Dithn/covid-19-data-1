import re

from bs4 import BeautifulSoup
import pandas as pd

from cowidev.utils.web import get_soup
from cowidev.vax.utils.incremental import enrich_data, increment


class Bahrain:
    location: str = "Bahrain"
    source_url: str = "https://healthalert.gov.bh/en/"

    def read(self) -> pd.Series:
        soup = get_soup(self.source_url)
        return self._parse_data(soup)

    def _parse_data(self, soup: BeautifulSoup) -> pd.Series:
        people_vaccinated = int(soup.find_all(class_="count")[0]["data-count"])
        people_fully_vaccinated = int(soup.find_all(class_="count")[1]["data-count"])
        booster_shots = int(soup.find_all(class_="count")[2]["data-count"])
        assert people_vaccinated >= people_fully_vaccinated
        total_vaccinations = people_vaccinated + people_fully_vaccinated + booster_shots

        date = soup.find(class_="reportdate").text
        date = re.search(r"\d+ \w+ 202\d", date).group(0)
        date = str(pd.to_datetime(date).date())

        data = {
            "total_vaccinations": total_vaccinations,
            "people_vaccinated": people_vaccinated,
            "people_fully_vaccinated": people_fully_vaccinated,
            "total_boosters": booster_shots,
            "date": date,
        }
        return pd.Series(data=data)

    def pipe_location(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "location", self.location)

    def pipe_vaccine(self, ds: pd.Series) -> pd.Series:
        return enrich_data(
            ds,
            "vaccine",
            "Oxford/AstraZeneca, Pfizer/BioNTech, Sinopharm/Beijing, Sputnik V",
        )

    def pipe_source(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "source_url", self.source_url)

    def pipeline(self, ds: pd.Series) -> pd.Series:
        return (
            ds.pipe(self.pipe_location)
            .pipe(self.pipe_vaccine)
            .pipe(self.pipe_source)[
                [
                    "location",
                    "date",
                    "vaccine",
                    "source_url",
                    "total_vaccinations",
                    "people_vaccinated",
                    "people_fully_vaccinated",
                    "total_boosters",
                ]
            ]
        )

    def export(self):
        data = self.read().pipe(self.pipeline)
        increment(
            location=data["location"],
            total_vaccinations=data["total_vaccinations"],
            people_vaccinated=data["people_vaccinated"],
            people_fully_vaccinated=data["people_fully_vaccinated"],
            total_boosters=data["total_boosters"],
            date=data["date"],
            source_url=data["source_url"],
            vaccine=data["vaccine"],
        )


def main():
    Bahrain().export()
