import pandas as pd

from cowidev.utils.clean.dates import localdate
from cowidev.utils.utils import check_known_columns
from cowidev.vax.utils.utils import build_vaccine_timeline
from cowidev.vax.utils.base import CountryVaxBase


class Peru(CountryVaxBase):
    location = "Peru"
    source_url = "https://github.com/jmcastagnetto/covid-19-peru-vacunas/raw/main/datos/vacunas_covid_resumen.csv"
    source_url_age = (
        "https://github.com/jmcastagnetto/covid-19-peru-vacunas/raw/main/datos/vacunas_covid_rangoedad_owid.csv"
    )
    source_url_manufacturer = (
        "https://github.com/jmcastagnetto/covid-19-peru-vacunas/raw/main/datos/vacunas_covid_fabricante.csv"
    )
    source_url_ref = "https://www.datosabiertos.gob.pe/dataset/vacunacion"
    vaccine_mapping = {
        "SINOPHARM": "Sinopharm/Beijing",
        "PFIZER": "Pfizer/BioNTech",
        "ASTRAZENECA": "Oxford/AstraZeneca",
        "MODERNA": "Moderna",
    }
    # Based on https://github.com/jmcastagnetto/covid-19-peru-vacunas/issues/5
    date_start = "2021-02-08"
    vax_timeline = None

    def read(self):
        df = pd.read_csv(self.source_url)
        check_known_columns(
            df, ["fecha_corte", "fecha_vacunacion", "fabricante", "dosis", "n_reg", "flag_vacunacion_general"]
        )
        return df[["fecha_vacunacion", "fabricante", "dosis", "n_reg", "flag_vacunacion_general"]]

    def read_manufacturer(self):
        return pd.read_csv(self.source_url_manufacturer)

    def pipe_rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.rename(columns={"fecha_vacunacion": "date", "fabricante": "vaccine"})
        return df.dropna(subset=["vaccine"])

    def pipe_filter_only_campaign(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df.flag_vacunacion_general].drop(columns=["flag_vacunacion_general"])

    def pipe_checks(self, df: pd.DataFrame) -> pd.DataFrame:
        # Check vaccine names
        unknown_vaccines = set(df["vaccine"].unique()).difference(self.vaccine_mapping.keys())
        if unknown_vaccines:
            raise ValueError("Found unknown vaccines: {}".format(unknown_vaccines))
        return df

    def pipe_get_vax_timeline(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.replace(self.vaccine_mapping)
        self.vax_timeline = df.groupby("vaccine").date.min().to_dict()
        return df

    def pipe_format(self, df: pd.DataFrame) -> pd.DataFrame:
        df.loc[df.dosis >= 3, "dosis"] = 3  # All doses from 3 onwards are boosters
        return (
            df.drop(columns="vaccine")
            .groupby(["date", "dosis"], as_index=False)
            .sum()
            .pivot(index="date", columns="dosis", values="n_reg")
            .rename(columns={1: "people_vaccinated", 2: "people_fully_vaccinated", 3: "total_boosters"})
            .fillna(0)
            .sort_values("date")
            .cumsum()
            .reset_index()
        )

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        df = build_vaccine_timeline(df, self.vax_timeline)
        return df

    def pipe_total_vaccinations(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(total_vaccinations=df.people_vaccinated + df.people_fully_vaccinated + df.total_boosters)

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(
            location=self.location,
            source_url=self.source_url_ref,
        )

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_filter_only_campaign)
            .pipe(self.pipe_checks)
            .pipe(self.pipe_get_vax_timeline)
            .pipe(self.pipe_format)
            .pipe(self.pipe_vaccine)
            .pipe(self.pipe_total_vaccinations)
            .pipe(self.pipe_metadata)
        )

    def read_age(self):
        df = pd.read_csv(self.source_url_age)
        check_known_columns(
            df,
            [
                "location",
                "fecha_corte",
                "epi_year",
                "epi_week",
                "last_day_of_epi_week",
                "complete_epi_week",
                "age_group_min",
                "age_group_max",
                "people_vaccinated_per_hundred",
                "people_fully_vaccinated_per_hundred",
                "people_receiving_booster_per_hundred",
                "people_receiving_second_booster_per_hundred",
                "people_receiving_third_booster_per_hundred",
            ],
        )
        return df

    def pipe_age_checks(self, df: pd.DataFrame) -> pd.DataFrame:
        # print(df.columns)
        if (msk := (df.people_vaccinated_per_hundred > 105)).sum():
            raise ValueError(f"Check `people_vaccinated_per_hundred` field! Found values above 100%. {df[msk]}")
        if (msk := (df.people_fully_vaccinated_per_hundred > 105)).sum():
            raise ValueError("Check `people_fully_vaccinated_per_hundred` field! Found values above 100%.")
        if not (df.location.unique() == self.location).all():
            raise ValueError("Invalid values in `location` field!")
        return df

    def pipe_age_date(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.rename(columns={"last_day_of_epi_week": "date"})
        df.loc[df.complete_epi_week == 0, "date"] = localdate("America/Lima")
        return df

    def pipe_age_columns_out(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns={"people_receiving_booster_per_hundred": "people_with_booster_per_hundred",})[
            [
                "location",
                "date",
                "age_group_min",
                "age_group_max",
                "people_vaccinated_per_hundred",
                "people_fully_vaccinated_per_hundred",
                "people_with_booster_per_hundred",
            ]
        ]

    def pipeline_age(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_age_checks).pipe(self.pipe_age_date).pipe(self.pipe_age_columns_out)

    def pipeline_manufacturer(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.pipe(self.pipe_filter_only_campaign)
        df = df.replace(self.vaccine_mapping).sort_values(["location", "date", "vaccine"])[
            ["location", "date", "vaccine", "total_vaccinations"]
        ]
        if not df.groupby("vaccine")["total_vaccinations"].is_monotonic_increasing.all():
            raise ValueError("Manufacturer data for Peru is not monotonically increasing!")
        return df

    def export(self):
        df = self.read().pipe(self.pipeline)
        # Age data
        df_age = self.read_age().pipe(self.pipeline_age)
        # Manufacturer data
        df_manuf = self.read_manufacturer().pipe(self.pipeline_manufacturer)
        # Export
        self.export_datafile(
            df=df,
            df_age=df_age,
            df_manufacturer=df_manuf,
            meta_age={
                "source_name": "Ministerio de Salud via https://github.com/jmcastagnetto/covid-19-peru-vacunas",
                "source_url": self.source_url_ref,
            },
            meta_manufacturer={
                "source_name": "Ministerio de Salud via https://github.com/jmcastagnetto/covid-19-peru-vacunas",
                "source_url": self.source_url_ref,
            },
        )


def main():
    Peru().export()
