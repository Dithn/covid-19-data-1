import pandas as pd

from cowidev.utils.clean.dates import localdate
from cowidev.vax.utils.incremental import enrich_data, increment
from cowidev.vax.utils.base import CountryVaxBase


class Finland(CountryVaxBase):
    location: str = "Finland"
    source_url: str = "https://sampo.thl.fi/pivot/prod/en/vaccreg/cov19cov/fact_cov19cov.csv?row=vacprod-533726&row=measure-533175.&column=cov_vac_dose-533174&"
    source_url_ref: str = "https://sampo.thl.fi/pivot/prod/en/vaccreg/cov19cov/fact_cov19cov"
    vaccine_mapping: dict = {
        "Comirnaty (BioNTech)": "Pfizer/BioNTech",
        "Spikevax (MODERNA)": "Moderna",
        "COVID-19 Vaccine Janssen (JANSSEN-CILAG)": "Johnson&Johnson",
        "Vaxzevria (AstraZeneca)": "Oxford/AstraZeneca",
    }
    metrics_mapping: dict = {
        "First dose": "people_vaccinated",
        "Second dose": "people_fully_vaccinated",
        "Booster dose": "total_boosters",
        "Third dose (NOT booster)": "third_dose",
    }

    def read(self) -> pd.Series:
        df = pd.read_csv(self.source_url, sep=";")
        return df

    def pipe_checks(self, df: pd.Series) -> pd.Series:
        self.check_column_values(
            df,
            "Vaccination dose",
            [
                "First dose",
                "Second dose",
                "Third dose",
                "Fourth dose",
                "All doses",
            ],
        )
        self.check_column_values(
            df,
            "Product",
            [
                "Comirnaty (BioNTech)",
                "Spikevax (MODERNA)",
                "Vaxzevria (AstraZeneca)",
                "Other products",
                "All products",
            ],
        )
        self.check_column_values(
            df,
            "Measure",
            [
                "Administered doses",
            ],
        )
        return df

    def pipe_clean(self, df: pd.DataFrame) -> pd.Series:
        # Keep only aggregate
        df = df[df.Product == "All products"]

        # Get metrics
        total_vaccinations = df[df["Vaccination dose"] == "All doses"].val.sum()
        people_vaccinated = df[df["Vaccination dose"] == "First dose"].val.sum()
        people_fully_vaccinated = df[df["Vaccination dose"] == "Second dose"].val.sum()
        total_boosters = df[df["Vaccination dose"].isin(["Third dose", "Fourth dose"])].val.sum()

        return pd.Series(
            {
                "total_vaccinations": total_vaccinations,
                "people_vaccinated": people_vaccinated,
                "people_fully_vaccinated": people_fully_vaccinated,
                "total_boosters": total_boosters,
            }
        )

    def pipe_date(self, ds: pd.Series) -> pd.Series:
        date = localdate("Europe/Helsinki")
        return enrich_data(ds, "date", date)

    def pipe_location(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "location", self.location)

    def pipe_vaccine(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "vaccine", "Moderna, Oxford/AstraZeneca, Pfizer/BioNTech")

    def pipe_source(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "source_url", self.source_url_ref)

    def pipeline(self, df: pd.DataFrame) -> pd.Series:
        return (
            df.pipe(self.pipe_checks)
            .pipe(self.pipe_clean)
            .pipe(self.pipe_date)
            .pipe(self.pipe_location)
            .pipe(self.pipe_vaccine)
            .pipe(self.pipe_source)
        )

    def export(self):
        data = self.read().pipe(self.pipeline)
        increment(
            location=data["location"],
            total_vaccinations=data["total_vaccinations"],
            people_vaccinated=data["people_vaccinated"],
            people_fully_vaccinated=data["people_fully_vaccinated"],
            total_boosters=data["total_boosters"],
            date=data["date"],
            source_url=data["source_url"],
            vaccine=data["vaccine"],
        )


def main():
    Finland().export()
