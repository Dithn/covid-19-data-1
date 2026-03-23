import requests
import pandas as pd

from cowidev.utils import clean_date
from cowidev.vax.utils.base import CountryVaxBase


class Slovenia(CountryVaxBase):
    location = "Slovenia"
    source_url = "https://api.sledilnik.org/api/vaccinations"
    source_url_ref = "https://covid-19.sledilnik.org/sl/stats"
    vaccine_mapping = {
        "pfizer": "Pfizer/BioNTech",
        "az": "Oxford/AstraZeneca",
        "moderna": "Moderna",
        "janssen": "Johnson&Johnson",
        "novavax": "Novavax",
    }

    def read(self):
        data = requests.get(self.source_url).json()
        df = self._parse_data(data)
        return df

    def _parse_data(self, data):
        data = [
            {
                "date": clean_date(f"{d['year']}-{d['month']}-{d['day']}", "%Y-%m-%d"),
                "total_vaccinations": d.get("usedToDate"),
                "people_vaccinated": d["administered"].get("toDate"),
                "people_fully_vaccinated": d["administered2nd"].get("toDate"),
                "total_boosters": d["administered3rd"].get("toDate"),
                "vaccine": self._build_vaccine_str(d),
            }
            for d in data
        ]
        df = pd.DataFrame(data)
        return df

    def _build_vaccine_str(self, d):
        return ", ".join(sorted([self.vaccine_mapping[v] for v in d["usedByManufacturer"].keys()]))

    def pipeline(self, df: pd.DataFrame):
        df = df.dropna(subset=["total_vaccinations", "people_vaccinated", "people_fully_vaccinated"], how="all")
        df = df.assign(
            location=self.location,
            source_url=self.source_url_ref,
        )
        return df

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Slovenia().export()
