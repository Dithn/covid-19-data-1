from bs4 import BeautifulSoup
import pandas as pd

from cowidev.utils.clean import clean_count
from cowidev.utils.clean.dates import localdate
from cowidev.utils.web import get_soup
from cowidev.vax.utils.incremental import enrich_data
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.utils import add_latest_who_values


class Moldova(CountryVaxBase):
    location = "Moldova"
    source_url = "https://vaccinare.gov.md"

    def read(self) -> pd.Series:
        soup = get_soup(self.source_url)
        return self._parse_data(soup)

    def _parse_data(self, soup: BeautifulSoup) -> pd.Series:

        total_vaccinations = clean_count(soup.find(id="stats").find_all("span")[0].text)
        people_fully_vaccinated = clean_count(soup.find(id="stats").find_all("span")[1].text)

        data = {
            "total_vaccinations": total_vaccinations,
            "people_fully_vaccinated": people_fully_vaccinated,
        }
        return pd.Series(data=data)

    def format_date(self, ds: pd.Series) -> pd.Series:
        date = localdate("Europe/Chisinau")
        return enrich_data(ds, "date", date)

    def enrich_location(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "location", "Moldova")

    def enrich_vaccine(self, ds: pd.Series) -> pd.Series:
        return enrich_data(
            ds,
            "vaccine",
            "Johnson&Johnson, Oxford/AstraZeneca, Pfizer/BioNTech, Sinopharm/Beijing, Sputnik V",
        )

    def enrich_source(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "source_url", self.source_url)

    def pipeline(self, ds: pd.Series) -> pd.Series:
        ds = ds.pipe(self.format_date).pipe(self.enrich_location).pipe(self.enrich_vaccine).pipe(self.enrich_source)
        df = add_latest_who_values(ds, "Republic of Moldova", ["people_vaccinated"])
        return df

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, attach=True)


def main():
    Moldova().export()
