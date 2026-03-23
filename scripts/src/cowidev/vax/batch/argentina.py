from cowidev.vax.utils.utils import build_vaccine_timeline
import requests

import pandas as pd

from cowidev.utils import clean_date
from cowidev.utils.clean.dates import clean_date_series
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.checks import VACCINES_ONE_DOSE
from cowidev.utils.utils import check_known_columns


class Argentina(CountryVaxBase):
    location = "Argentina"
    source_url = "https://covidstats.com.ar/ws/vacunadosargentina?portipovacuna=1"
    source_url_age = "https://covidstats.com.ar/ws/vacunadosargentina?porgrupoetario=1"
    source_url_ref = "https://covidstats.com.ar/"
    age_group_valid = {
        "30-39",
        "80-89",
        "18-29",
        "90-99",
        "50-59",
        "70-79",
        "60-69",
        ">=100",
        "40-49",
        "<12",
        "12-17",
    }
    vaccine_mapping = {
        "Cansino Ad5 nCoV": "CanSino",
        "Sputnik V COVID19 Instituto Gamaleya": "Sputnik V",
        "Moderna ARNm": "Moderna",
        "Moderna Pediátrica": "Moderna",
        "Moderna ARNm 020 mg mL": "Moderna",
        "Moderna 010 mg mL": "Moderna",
        "Pfizer Pediátrica": "Pfizer/BioNTech",
        "COVISHIELD ChAdOx1nCoV COVID 19": "Oxford/AstraZeneca",
        "Pfizer BioNTech Comirnaty": "Pfizer/BioNTech",
        "AstraZeneca ChAdOx1 S recombinante": "Oxford/AstraZeneca",
        "Sinopharm Vacuna SARSCOV 2 inactivada": "Sinopharm/Beijing",
        "Pfizer Bivariante BA 4 5": "Pfizer/BioNTech",
        "Sputnik Light": "Sputnik Light",
        "Moderna Bivariante BA 4 5": "Moderna",
    }

    def read(self):
        data = requests.get(self.source_url).json()
        data = list(data.values())
        if data[-1] == True:
            data = data[:-1]
        else:
            raise ValueError("Source data format changed!")
        data = self._parse_data(data)
        return data

    def read_age(self):
        data = requests.get(self.source_url_age).json()
        data = list(data.values())[:-1]
        self._check_data_age(data)
        data = self._parse_data_age(data)
        return data

    def _parse_data(self, data):
        # Merge
        dfs = [self._build_df(d) for d in data]
        df = pd.concat(dfs, ignore_index=True).assign(location=self.location)
        return df

    def _build_df(self, data):
        # Check columns
        columns_expected = {
            "fecha_inicial",
            "denominacion",
            "dosis1",
            "dosis2",
            "adicional",
            "esquemacompleto",
            "refuerzo",
            "dias",
        }
        columns_unknown = set(data.keys()).difference(columns_expected)
        if columns_unknown:
            raise ValueError(f"Unknown columns detected! {columns_unknown}")
        # Get dates
        dt = clean_date(data["fecha_inicial"], "%Y-%m-%dT%H:%M:%S%z", as_datetime=False)
        dates = pd.date_range(dt, periods=data["dias"], freq="D")
        # Build df
        # Notes on differences adicional vs refuerzo:
        # https://github.com/owid/covid-19-data/issues/2532#issuecomment-1074137207
        df = pd.DataFrame(
            {
                "date": clean_date_series(list(dates)),
                "vaccine": data["denominacion"],
                "dose_1": data["dosis1"],
                "dose_2": data["dosis2"],
                "dose_additional": data["adicional"],
                "people_fully_vaccinated": data["esquemacompleto"],
                "total_boosters": data["refuerzo"],
            }
        )
        return df

    def pipe_base_vaccines(self, df: pd.DataFrame):
        vaccines_wrong = set(df.vaccine).difference(self.vaccine_mapping)
        if vaccines_wrong:
            raise ValueError(f"Unknown vaccines detected! {vaccines_wrong}")
        df = df.assign(vaccine=df.vaccine.replace(self.vaccine_mapping))
        df = df.groupby(["date", "vaccine"], as_index=False).sum()
        return df

    def pipe_base_cumsum(self, df: pd.DataFrame):
        cols = ["dose_1", "dose_2", "dose_additional", "people_fully_vaccinated", "total_boosters"]
        df[cols] = df.sort_values("date").groupby("vaccine")[cols].cumsum()
        return df

    def pipe_base_metrics(self, df):
        # Split df by single/two dose protocols
        msk = df.vaccine.isin(VACCINES_ONE_DOSE)
        df_2d = df[~msk]
        df_1d = df[msk]
        # Estimate metrics
        df_2d = df_2d.assign(
            total_vaccinations=df.dose_1 + df.dose_2 + df.dose_additional + df.total_boosters,
            people_vaccinated=df.dose_1,
            total_boosters=df.dose_additional + df.total_boosters,
        )
        df_1d = df_1d.assign(
            total_vaccinations=df.dose_1 + df.dose_2 + df.dose_additional + df.total_boosters,
            people_vaccinated=df.dose_1,
            total_boosters=df.dose_2 + df.dose_additional + df.total_boosters,
        )
        # Single dose check
        if not (df_1d.people_fully_vaccinated == df_1d.people_vaccinated).all():
            raise ValueError(
                "Something wrong with single-dose vaccines! We should have that `people_vaccinated =="
                " people_fully_vaccinated`"
            )
        df = pd.concat([df_1d, df_2d], ignore_index=True).sort_values(["date", "vaccine"])
        # Only report when total_Vaccinations > 0
        df = df[df.total_vaccinations > 0]
        return df[
            ["date", "vaccine", "total_vaccinations", "people_vaccinated", "people_fully_vaccinated", "total_boosters"]
        ]

    def pipe_aggregate_vaccines(self, df: pd.DataFrame):
        return df.groupby("date", as_index=False).sum()

    def pipe_vaccine(self, df: pd.DataFrame):
        return build_vaccine_timeline(
            df,
            {
                "Sputnik V": "2020-12-29",
                "Sinopharm/Beijing": "2021-03-08",
                "Oxford/AstraZeneca": "2021-03-08",
                "Moderna": "2021-08-03",
                "CanSino": "2021-09-09",
                "Pfizer/BioNTech": "2021-09-17",
            },
        )

    def _check_data_age(self, data):
        ages = {d["denominacion"] for d in data}
        age_wrong = ages.difference(self.age_group_valid | {"Otros (sin especificar)"})
        if age_wrong:
            raise ValueError(f"Unknown age group {age_wrong}")

    def _parse_data_age(self, data):
        # Merge
        dfs = [self._build_df_age_group(d) for d in data if d["denominacion"] in self.age_group_valid]
        df = pd.concat(dfs, ignore_index=True).assign(location=self.location)
        df[["age_group_min", "age_group_max"]] = df[["age_group_min", "age_group_max"]].astype(str)
        return df

    def _build_df_age_group(self, data):
        # Get dates
        dt = clean_date(data["fecha_inicial"], "%Y-%m-%dT%H:%M:%S%z", as_datetime=False)
        dates = pd.date_range(dt, periods=data["dias"], freq="D")
        # Build df
        df = pd.DataFrame(
            {
                "date": dates,
                "people_vaccinated": data["dosis1"],
                "people_fully_vaccinated": data["esquemacompleto"],
                # "people_with_booster": [d + b for d, b in zip(data["refuerzo"], data["adicional"])],
                "people_with_booster": data[
                    "refuerzo"
                ],  # likely an under estimate (missing doses for immunocompromised)
            }
        ).assign(
            **{
                "age_group_min": data["desdeedad"],
                "age_group_max": data["hastaedad"] if data["hastaedad"] is not None else "",
                "age_group": data["denominacion"],
            }
        )
        return df

    def pipe_age_cumsum(self, df):
        # cumsum
        cols = ["people_vaccinated", "people_fully_vaccinated", "people_with_booster"]
        df[cols] = df.sort_values("date").groupby("age_group")[cols].cumsum()
        return df

    def pipe_age_date(self, df):
        return df.assign(date=clean_date_series(df.date))

    def pipeline_base(self, df: pd.DataFrame):
        return df.pipe(self.pipe_base_vaccines).pipe(self.pipe_base_cumsum).pipe(self.pipe_base_metrics)

    def pipeline(self, df: pd.DataFrame) -> pd.Series:
        return df.pipe(self.pipe_aggregate_vaccines).pipe(self.pipe_metadata).pipe(self.pipe_vaccine)

    def pipeline_manufacturer(self, df: pd.DataFrame) -> pd.Series:
        df = df.assign(location="Argentina")[["location", "date", "vaccine", "total_vaccinations"]]
        return df

    def pipeline_age(self, df):
        return df.pipe(self.pipe_age_cumsum).pipe(self.pipe_age_date).pipe(self.pipe_age_per_capita)

    def export(self):
        # Base data
        df_base = self.read().pipe(self.pipeline_base)
        # Main data
        df = df_base.pipe(self.pipeline)
        # Manufacturer data
        df_man = df_base.pipe(self.pipeline_manufacturer)
        # Age data
        df_age = self.read_age().pipe(self.pipeline_age)
        # Export
        self.export_datafile(
            df=df,
            df_age=df_age,
            df_manufacturer=df_man,
            meta_age={
                "source_name": f"Ministry of Health via {self.source_url}",
                "source_url": self.source_url_ref,
            },
            meta_manufacturer={
                "source_name": f"Ministry of Health via {self.source_url}",
                "source_url": self.source_url_ref,
            },
        )


def main():
    Argentina().export()
