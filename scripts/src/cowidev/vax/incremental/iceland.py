import re
import json

import pandas as pd

from cowidev.utils import get_soup, clean_count, clean_date_series
from cowidev.vax.utils.incremental import increment
from cowidev.vax.utils.base import CountryVaxBase


VACCINE_PROTOCOLS = {
    "Pfizer": 2,
    "Moderna": 2,
    "AstraZeneca": 2,
    "Janssen": 1,
}

VACCINE_MAPPING = {
    "Pfizer/BioNTech": "Pfizer/BioNTech",
    "Moderna": "Moderna",
    "Oxford/AstraZeneca": "Oxford/AstraZeneca",
    "Janssen": "Johnson&Johnson",
}


class Iceland(CountryVaxBase):
    location: str = "Iceland"
    source_url: str = "https://e.infogram.com/c3bc3569-c86d-48a7-9d4c-377928f102bf"
    source_url_ref: str = "https://www.covid.is/tolulegar-upplysingar-boluefni"
    metric_entities: dict = {
        "total_vaccinations": "7287c058-7921-4abc-a667-ce298827c969",
        "people_vaccinated": "8d14f33a-d482-4176-af55-71209314b07b",
        "people_fully_vaccinated": "16a69e30-01fd-4806-920c-436f8f29e9bf",
        "total_boosters": "209af2de-9927-4c51-a704-ddc85e28bab9",
        "additional_doses": "c1286d9e-254c-434a-9455-21b94969d163",
    }

    def read(self):
        soup = get_soup(self.source_url)
        json_data = self._get_json_data(soup)
        data = self._parse_data(json_data)
        df_manuf = self._parse_data_manufacturer(json_data)
        return data, df_manuf

    def _parse_data_manufacturer(self, json_data):
        data = json_data["elements"]["content"]["content"]["entities"]["e329559c-c3cc-48e9-8b7b-1a5f87ea7ad3"][
            "props"
        ]["chartData"]["data"][0]
        df = pd.DataFrame(data[1:]).reset_index(drop=True)
        df.columns = ["date"] + data[0][1:]
        return df

    def _parse_data(self, json_data):
        data = {**self._parse_metrics(json_data), "date": self._parse_date(json_data)}
        return data

    def _get_json_data(self, soup):
        for script in soup.find_all("script"):
            if "infographicData" in str(script):
                json_data = str(script).replace("<script>window.infographicData=", "").replace(";</script>", "")
                json_data = json.loads(json_data)
                break
        return json_data

    def _parse_metrics(self, json_data):
        data = {}
        for metric, entity in self.metric_entities.items():
            value = json_data["elements"]["content"]["content"]["entities"][entity]["props"]["chartData"]["data"][0][
                0
            ][0]
            value = re.search(r'18px;">([\d\.]+)', value).group(1)
            value = clean_count(value)
            data[metric] = value
        return data

    def _parse_date(self, json_data):
        date = json_data["updatedAt"][:10]
        return date

    def pipeline_manufacturer(self, df):
        df = df.melt("date", var_name="vaccine", value_name="total_vaccinations")
        df["date"] = clean_date_series(df["date"], "%d.%m.%Y")
        df["total_vaccinations"] = pd.to_numeric(df["total_vaccinations"], errors="coerce").fillna(0)
        df["total_vaccinations"] = (
            df.sort_values("date").groupby("vaccine", as_index=False)["total_vaccinations"].cumsum()
        )
        df["location"] = "Iceland"
        assert set(df["vaccine"].unique()) == set(
            VACCINE_MAPPING.keys()
        ), f"Vaccines present in data: {df['vaccine'].unique()}"
        df = df.replace(VACCINE_MAPPING)
        return df

    def export(self):
        data, df_manuf = self.read()
        # Main
        increment(
            location=self.location,
            total_vaccinations=data["total_vaccinations"],
            people_vaccinated=data["people_vaccinated"],
            people_fully_vaccinated=data["people_fully_vaccinated"],
            total_boosters=data["total_boosters"] + data["additional_doses"],
            date=data["date"],
            source_url=self.source_url_ref,
            vaccine=", ".join(sorted(VACCINE_MAPPING.values())),
        )
        # By manufacturer
        df_manuf = df_manuf.pipe(self.pipeline_manufacturer).dropna(subset=["date"])
        self.export_datafile(
            df_manufacturer=df_manuf,
            meta_manufacturer={
                "source_name": "Ministry of Health",
                "source_url": self.source_url,
            },
        )


def main():
    Iceland().export()
