import datetime

import pandas as pd
import requests

from cowidev.utils.clean import clean_date_series
from cowidev.vax.utils.utils import build_vaccine_timeline
from cowidev.vax.utils.base import CountryVaxBase


class Ukraine(CountryVaxBase):
    # it is expected to use Novavax vaccine as well in future,
    # if so, this script should be updated
    source_url: str = "https://health-security.rnbo.gov.ua"
    source_api_url: str = "https://health-security.rnbo.gov.ua/api/vaccination/process/chart"
    location: str = "Ukraine"
    vaccines_mapping: dict = {
        "Moderna": "Moderna",
        "AstraZeneca": "Oxford/AstraZeneca",
        "Pfizer-BioNTech": "Pfizer/BioNTech",
        "Johnson & Johnson": "Johnson&Johnson",
        "Sinovac (CoronaVac)": "Sinovac",
    }

    def _load_dose_data(self, dose_param, colname):
        # if colname
        doses_api = requests.get(f"{self.source_api_url}?dose={dose_param}").json()

        vax_wrong = set(doses_api["daily"]["cumulative"].keys()).difference(self.vaccines_mapping)
        # if vax_wrong:
        #     raise ValueError(f"Unknown vaccines! {vax_wrong}")  Raising error bc of 'SarsCov2_nRVv3'

        df = pd.DataFrame(
            {
                "date": [datetime.datetime.strptime(x, "%Y-%m-%d") for x in doses_api["daily"]["dates"]],
                f"{colname}_moderna": doses_api["daily"]["cumulative"]["Moderna"],
                f"{colname}_astrazeneca": doses_api["daily"]["cumulative"]["AstraZeneca"],
                f"{colname}_pfizer": doses_api["daily"]["cumulative"]["Pfizer-BioNTech"],
                f"{colname}_jnj": doses_api["daily"]["cumulative"].get("Johnson & Johnson", 0),
                f"{colname}_sinovac": doses_api["daily"]["cumulative"]["Sinovac (CoronaVac)"],
            },
        )

        if dose_param == "2":
            df[f"{colname}_jnj"] = 0

        df[f"{colname}_total"] = (
            df[f"{colname}_moderna"]
            + df[f"{colname}_astrazeneca"]
            + df[f"{colname}_pfizer"]
            + df[f"{colname}_jnj"]
            + df[f"{colname}_sinovac"]
        )

        return df

    def read(self):
        # Read doses
        first_dose_df = self._load_dose_data(dose_param="1", colname="first_dose")
        second_dose_df = self._load_dose_data(dose_param="2", colname="second_dose")
        additional_dose_df = self._load_dose_data(dose_param="A", colname="additional_dose")
        booster_dose_df = self._load_dose_data(dose_param="3", colname="third_dose")
        # Build df
        booster_df = booster_dose_df.join(additional_dose_df.set_index("date"), on=["date"])
        main_df = first_dose_df.join(second_dose_df.set_index("date"), on=["date"])
        total_df = main_df.join(booster_df.set_index("date"), on=["date"])

        for col in ["total", "moderna", "astrazeneca", "pfizer", "jnj", "sinovac"]:
            total_df[f"booster_dose_{col}"] = total_df[f"third_dose_{col}"] + total_df[f"additional_dose_{col}"]

            total_df[f"all_doses_{col}"] = (
                total_df[f"first_dose_{col}"] + total_df[f"second_dose_{col}"] + total_df[f"booster_dose_{col}"]
            )

        total_df = total_df.assign(location=self.location, source_url=self.source_url)
        return total_df

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        df["date"] = clean_date_series(df["date"])
        return df

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        df = build_vaccine_timeline(
            df,
            {
                "Oxford/AstraZeneca": "2021-01-01",
                "Sinovac": "2021-04-14",
                "Pfizer/BioNTech": "2021-04-18",
                "Johnson&Johnson": "2021-05-22",
                "Moderna": "2021-07-23",
            },
        )
        return df

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(
            total_vaccinations=df["second_dose_total"] + df["first_dose_total"] + df["booster_dose_total"],
            people_vaccinated=df["first_dose_total"],
            people_fully_vaccinated=df["second_dose_total"] + df["first_dose_jnj"],
            total_boosters=df["booster_dose_total"],
        )

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_date)
            .pipe(self.pipe_vaccine)
            .pipe(self.pipe_metrics)[
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
            .sort_values(["date"])
        )

    def pipeline_manufacturer(self, df: pd.DataFrame) -> pd.DataFrame:
        vaccine_columns = {
            "Oxford/AstraZeneca": "all_doses_astrazeneca",
            "Sinovac": "all_doses_sinovac",
            "Pfizer/BioNTech": "all_doses_pfizer",
            "Johnson&Johnson": "all_doses_jnj",
            "Moderna": "all_doses_moderna",
        }

        vac_dfs = []
        for vaccine, col in vaccine_columns.items():
            vac_df = df[["location", "date", col]].copy()
            vac_df["vaccine"] = vaccine
            vac_df.rename(columns={col: "total_vaccinations"}, inplace=True)
            vac_df = vac_df[vac_df["total_vaccinations"] > 0]
            vac_dfs.append(vac_df[["location", "date", "vaccine", "total_vaccinations"]])

        return pd.concat(vac_dfs, ignore_index=True).sort_values(["date", "vaccine"])

    def export(self):
        # Load data
        df_base = self.read()
        # Main data
        df = df_base.pipe(self.pipeline)
        # Manufacturer data
        df_man = df_base.pipe(self.pipeline_manufacturer)
        self.export_datafile(
            df,
            df_manufacturer=df_man,
            meta_manufacturer={
                "source_name": "National Security and Defense Council of Ukraine",
                "source_url": self.source_url,
            },
        )


def main():
    Ukraine().export()
