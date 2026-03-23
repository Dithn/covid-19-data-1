import pandas as pd

from cowidev.utils.clean import clean_count
from cowidev.utils.clean.dates import localdate
from cowidev.utils.web.scraping import get_soup
from cowidev.vax.utils.incremental import enrich_data
from cowidev.vax.utils.base import CountryVaxBase


class Jamaica(CountryVaxBase):
    location: str = "Jamaica"
    source_url: str = "https://vaccination.moh.gov.jm"
    source_url_ref: str = source_url

    def read(self) -> pd.Series:
        soup = get_soup(self.source_url)
        return self._parse_data(soup)

    def _parse_data(self, soup) -> pd.Series:
        counters = soup.find_all(class_="service-title")
        assert len(counters) == 6, "New counter in dashboard?"
        total_vaccinations = clean_count(counters[0].text.replace(" ", ""))
        first_doses = clean_count(counters[1].text)
        second_doses = clean_count(counters[2].text)
        unique_doses = clean_count(counters[3].text)
        immunocompromised_doses = clean_count(counters[4].text)
        booster_shots = clean_count(counters[5].text)

        people_vaccinated = first_doses + unique_doses
        people_fully_vaccinated = second_doses + unique_doses
        total_boosters = booster_shots + immunocompromised_doses

        date = localdate("America/Jamaica")

        return pd.Series(
            data={
                "total_vaccinations": total_vaccinations,
                "people_vaccinated": people_vaccinated,
                "people_fully_vaccinated": people_fully_vaccinated,
                "total_boosters": total_boosters,
                "date": date,
            }
        )

    def pipe_vaccine(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "vaccine", "Johnson&Johnson, Moderna, Pfizer/BioNTech, Oxford/AstraZeneca")

    def pipeline(self, ds: pd.Series) -> pd.Series:
        return ds.pipe(self.pipe_vaccine).pipe(self.pipe_metadata)

    def export(self):
        data = self.read().pipe(self.pipeline)
        self.export_datafile(df=data, attach=True)


def main():
    Jamaica().export()
