import pandas as pd

from cowidev.utils.clean import clean_date_series
from cowidev.utils.utils import check_known_columns
from cowidev.vax.utils.utils import build_vaccine_timeline
from cowidev.vax.utils.base import CountryVaxBase


class Ecuador(CountryVaxBase):
    location = "Ecuador"
    source_url_ref = "https://github.com/andrab/ecuacovid"
    source_url = {
        "manufacturer": f"{source_url_ref}/raw/master/datos_crudos/vacunometro/fabricantes.csv",
        "main": f"{source_url_ref}/raw/master/datos_crudos/vacunas/vacunas.csv",
    }
    columns_rename_manuf = {
        "fabricante": "vaccine",
        "dosis_total": "total_vaccinations",
        "administered_at": "date",
    }
    columns_rename = {
        "fecha": "date",
        "dosis_total": "total_vaccinations",
        "primera_dosis": "people_vaccinated",
        "segunda_dosis": "people_fully_vaccinated",
        "dosis_unica": "single_shots",
        "refuerzo_1": "boosters_1",
        "refuerzo_2": "boosters_2",
    }
    vaccine_mapping = {
        "Pfizer/BioNTech": "Pfizer/BioNTech",
        "Sinovac": "Sinovac",
        "Oxford/AstraZeneca": "Oxford/AstraZeneca",
        "CanSino": "CanSino",
    }
    vax_timeline = {
        "Pfizer/BioNTech": "2020-12-01",
        "Sinovac": "2021-03-06",
        "Oxford/AstraZeneca": "2021-03-17",
        "CanSino": "2021-08-03",
    }

    def read_manuf(self) -> pd.DataFrame:
        return pd.read_csv(self.source_url["manufacturer"])

    def pipe_manuf_rename_cols(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns=self.columns_rename_manuf)

    def pipe_manuf_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        # Aggregate zones
        return df.groupby(["vaccine", "date"], as_index=False).sum()

    def pipe_manuf_vaccine_checks(self, df: pd.DataFrame) -> pd.DataFrame:
        # Check vaccines
        vaccines_wrong = set(df.vaccine).difference(self.vaccine_mapping)
        if vaccines_wrong:
            raise ValueError(f"Unknown vaccine(s) {vaccines_wrong}")
        return df

    def pipe_manuf_date(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(date=clean_date_series(df.date, format_input="%d/%m/%Y"))

    def pipeline_manufacturer(self, df: pd.DataFrame) -> pd.DataFrame:
        check_known_columns(
            df,
            [
                "zona",
                "fabricante",
                "dosis_total",
                "primera_dosis",
                "segunda_dosis",
                "dosis_unica",
                "dosis_refuerzo",
                "administered_at",
            ],
        )
        return (
            df.pipe(self.pipe_manuf_rename_cols)
            .pipe(self.pipe_manuf_aggregate)
            .pipe(self.pipe_manuf_vaccine_checks)
            .pipe(self.pipe_manuf_date)
            .assign(location=self.location)
            .pipe(self.make_monotonic, ["vaccine"])
            .sort_values(["vaccine", "date"])[["location", "date", "vaccine", "total_vaccinations"]]
        )

    def read(self) -> pd.DataFrame:
        df = pd.read_csv(self.source_url["main"])
        return df

    def pipe_column_rename(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns=self.columns_rename)

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(
            people_vaccinated=df.people_vaccinated + df.single_shots,
            people_fully_vaccinated=df.people_fully_vaccinated + df.single_shots,
            total_boosters=df.boosters_1 + df.boosters_2,
        )

    def pipe_checks(self, df: pd.DataFrame) -> pd.DataFrame:
        return df

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(date=clean_date_series(df.date, "%d/%m/%Y"))

    def pipe_vaccines(self, df: pd.DataFrame) -> pd.DataFrame:
        return build_vaccine_timeline(df, self.vax_timeline)

    def pipe_exclude_dp(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[(df.date < "2021-09-01") | (df.date > "2021-09-07")]

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        check_known_columns(
            df,
            ["fecha", "dosis_total", "primera_dosis", "segunda_dosis", "dosis_unica", "refuerzo_1", "refuerzo_2"],
        )
        return (
            df.pipe(self.pipe_column_rename)
            .pipe(self.pipe_metrics)
            .pipe(self.pipe_checks)
            .pipe(self.pipe_date)
            .pipe(self.pipe_vaccines)
            .assign(location=self.location, source_url=self.source_url_ref)[
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
            .sort_values("date")
            .pipe(self.pipe_exclude_dp)
            .pipe(make_monotonic)
        )

    def export(self):
        # Manufacturer
        df_man = self.read_manuf().pipe(self.pipeline_manufacturer)
        # Main
        df = self.read().pipe(self.pipeline)
        # Export
        self.export_datafile(
            df=df,
            df_manufacturer=df_man,
            meta_manufacturer={
                "source_name": f"Ministerio de Salud Pública del Ecuador (via {self.source_url_ref})",
                "source_url": self.source_url_ref,
            },
        )


def main():
    Ecuador().export()
