import re

import pandas as pd

from cowidev.utils.clean import clean_count
from cowidev.utils.web.scraping import get_soup
from cowidev.vax.utils.incremental import enrich_data, increment
from cowidev.vax.utils.base import CountryVaxBase


class Pakistan(CountryVaxBase):
    location = "Pakistan"
    source_url = "https://covid.gov.pk/vaccine-details"
    source_url_ref = source_url

    def read(self):
        soup = get_soup(self.source_url)
        return pd.Series(data=self._parse_data(soup))

    def _parse_data(self, soup):
        counters = soup.find_all(class_="counter-main")
        people_vaccinated = clean_count(counters[0].text)
        people_fully_vaccinated = clean_count(counters[1].text)
        total_boosters = clean_count(counters[2].text)
        total_vaccinations = clean_count(counters[3].text)

        date = soup.find("span", id="last-update").text
        date = re.search(r"\d+.*202\d", date).group(0)
        date = str((pd.to_datetime(date) - pd.Timedelta(days=1)).date())

        data = {
            "total_vaccinations": total_vaccinations,
            "people_vaccinated": people_vaccinated,
            "people_fully_vaccinated": people_fully_vaccinated,
            "total_boosters": total_boosters,
            "date": date,
            "source_url": self.source_url,
        }

        return data

    def pipe_vaccine(self, ds: pd.Series) -> pd.Series:
        return enrich_data(
            ds,
            "vaccine",
            "CanSino, Covaxin, Moderna, Oxford/AstraZeneca, Pfizer/BioNTech, Sinopharm/Beijing, Sinovac, Sputnik V",
        )

    def pipeline(self, ds: pd.Series) -> pd.Series:
        return ds.pipe(self.pipe_vaccine).pipe(self.pipe_metadata)

    def export(self):
        data = self.read().pipe(self.pipeline)
        self.export_datafile(df=data, attach=True)


def main():
    Pakistan().export()
