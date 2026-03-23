import re

import pandas as pd

from cowidev.utils import clean_count, get_soup
from cowidev.utils.clean.dates import extract_clean_date
from cowidev.vax.utils.incremental import enrich_data, increment


class Greenland:
    location: str = "Greenland"
    source_url: str = "https://corona.nun.gl/en/"
    regex = {"date": r".*Nutarterneqarpoq: (\d+. [a-zA-Z]+202\d)"}

    def read(self) -> pd.Series:
        soup = get_soup(self.source_url)
        data = self._parse_data(soup)
        return pd.Series(data=data)

    def _parse_data(self, soup) -> dict:
        return {**self._parse_data_metrics(soup), **self._parse_data_date(soup)}

    def _parse_data_metrics(self, soup) -> dict:
        # Find raw elements with metric values
        regex_dose1 = (
            r"flex flex-col border-t border-b border-gray-100 p-6 text-center sm:border-0 sm:border-l sm:border-r"
        )
        regex_dose2 = r"flex flex-col border-t border-gray-100 p-6 text-center sm:border-0 sm:border-l"
        counter_1 = soup.find_all(class_=regex_dose1)
        counter_2 = soup.find_all(class_=regex_dose2)
        assert len(counter_1) == len(counter_2) == 1
        counter_1, counter_2 = counter_1[0], counter_2[0]
        # Extract metric falues
        dose_1 = clean_count(re.search(r".* ([\d\.]*) citizens", counter_1.text).group(1))
        dose_2 = clean_count(re.search(r".* ([\d\.]*) citizens", counter_2.text).group(1))
        return {"people_vaccinated": dose_1, "people_fully_vaccinated": dose_2}

    def _parse_data_date(self, soup) -> dict:
        regex = r"mt-4 sm:mt-6 text-sm text-center text-gray-500"
        counter_date = soup.find_all(class_=regex)
        assert len(counter_date) == 1
        counter_date = counter_date[0]
        date = extract_clean_date(counter_date.text, r".* Updated (\d*\. [A-Z][a-z]*)", "%d. %B", replace_year=2022)
        return {"date": date}

    def pipe_source(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "source_url", self.source_url)

    def pipe_vaccine(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "vaccine", "Moderna")

    def pipe_location(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "location", self.location)

    def pipe_metrics(self, ds: pd.Series) -> pd.Series:
        total_vaccinations = ds["people_vaccinated"] + ds["people_fully_vaccinated"]
        return enrich_data(ds, "total_vaccinations", total_vaccinations)

    def pipeline(self, ds: pd.Series) -> pd.Series:
        return ds.pipe(self.pipe_location).pipe(self.pipe_vaccine).pipe(self.pipe_source).pipe(self.pipe_metrics)

    def export(self):
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
    Greenland().export()
