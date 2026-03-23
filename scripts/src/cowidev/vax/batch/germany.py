import re
from cowidev.vax.utils.base import CountryVaxBase

import pandas as pd

from cowidev.vax.utils.utils import build_vaccine_timeline


class Germany(CountryVaxBase):
    source_url: str = "https://impfdashboard.de/static/data/germany_vaccinations_timeseries_v3.tsv"
    source_url_ref: str = "https://impfdashboard.de/"
    location: str = "Germany"
    columns_rename: str = {
        "impfungen_kumulativ": "total_vaccinations",
        "personen_min1_kumulativ": "people_vaccinated",
        "personen_gi_kumulativ": "people_fully_vaccinated",
        "impfungen_boost1_kumulativ": "total_boosters",
        "impfungen_boost2_kumulativ": "total_boosters_2",
    }
    vaccine_mapping: str = {
        "impfungen_biontech_kumulativ": "Pfizer/BioNTech",
        "impfungen_moderna_kumulativ": "Moderna",
        "impfungen_astra_kumulativ": "Oxford/AstraZeneca",
        "impfungen_johnson_kumulativ": "Johnson&Johnson",
        "impfungen_novavax_kumulativ": "Novavax",
        "impfungen_valneva_kumulativ": "Valneva",
        # "impfungen_sanofi_kumulativ": "Sanofi/GSK",
    }
    fully_vaccinated_mapping: str = {
        "impfungen_biontech_gi_kumulativ": "full_biontech",
        "impfungen_moderna_gi_kumulativ": "full_moderna",
        "impfungen_johnson_gi_kumulativ": "full_jj",
        "impfungen_astra_gi_kumulativ": "full_astra",
        "impfungen_novavax_gi_kumulativ": "full_nova",
    }
    regex_doses_colnames: str = r"impfungen_([a-zA-Z]*)_kumulativ"

    def read(self):
        return pd.read_csv(self.source_url, sep="\t")

    def _check_vaccines(self, df: pd.DataFrame):
        """Get vaccine columns mapped to Vaccine names."""
        EXCLUDE = ["min1", "gi", "boost1", "boost2"]

        def _is_vaccine_column(column_name: str):
            if re.search(self.regex_doses_colnames, column_name):
                if re.search(self.regex_doses_colnames, column_name).group(1) not in EXCLUDE:
                    return True
            return False

        for column_name in df.columns:
            if _is_vaccine_column(column_name) and column_name not in self.vaccine_mapping:
                raise ValueError(f"Found unknown vaccine: {column_name}")
        return df

    def translate_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns=self.columns_rename)

    def translate_vaccine_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns=self.vaccine_mapping).rename(columns=self.fully_vaccinated_mapping)

    def calculate_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(
            # people_fully_vaccinated=df.full_biontech + df.full_moderna + df.full_jj + df.full_astra + df.full_nova,
            total_boosters=df.total_boosters
            + df.total_boosters_2,
        )

    def enrich_location(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(location="Germany")

    def pipeline_base(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self._check_vaccines)
            .pipe(self.translate_columns)
            .pipe(self.translate_vaccine_columns)
            .pipe(self.calculate_metrics)
            .pipe(self.enrich_location)
        )

    def enrich_source(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(source_url=self.source_url_ref)

    def _vaccine_start_dates(self, df: pd.DataFrame):
        vax_timeline = df[["date"] + [*self.vaccine_mapping.values()]].melt(id_vars="date")
        vax_timeline = (
            vax_timeline[vax_timeline.value > 0].drop(columns="value").groupby("variable").min().to_dict()["date"]
        )
        return vax_timeline

    def enrich_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        vax_timeline = self._vaccine_start_dates(df)
        return build_vaccine_timeline(df, vax_timeline)

    def select_output_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[
            [
                "date",
                "location",
                "vaccine",
                "source_url",
                "total_vaccinations",
                "people_vaccinated",
                "people_fully_vaccinated",
                "total_boosters",
            ]
        ]

    def pipe_sanity_checks(self, df: pd.DataFrame) -> pd.DataFrame:
        # There were some issues with the file on Dec 28, 2021 (all Pfizer doses have been removed)
        # I've introduced some basic value checks here to make sure very low values can't go through
        assert df.total_vaccinations.max() > 140000000
        assert df.people_vaccinated.max() > 60000000
        assert df.people_fully_vaccinated.max() > 50000000
        assert df.people_vaccinated.max() > 25000000
        return df

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.enrich_source)
            .pipe(self.enrich_vaccine)
            .pipe(self.select_output_columns)
            .pipe(self.pipe_sanity_checks)
        )

    def melt_manufacturers(self, df: pd.DataFrame) -> pd.DataFrame:
        id_vars = ["date", "location"]
        return df[id_vars + list(self.vaccine_mapping.values())].melt(
            id_vars=id_vars, var_name="vaccine", value_name="total_vaccinations"
        )

    def pipeline_manufacturer(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.melt_manufacturers)

    def export(self):
        df_base = self.read().pipe(self.pipeline_base)
        # Main data
        df = df_base.pipe(self.pipeline)
        # Manufacturer data
        df_man = df_base.pipe(self.pipeline_manufacturer)
        # Export
        self.export_datafile(
            df,
            df_manufacturer=df_man,
            meta_manufacturer={"source_name": "Robert Koch Institut", "source_url": self.source_url_ref},
        )


def main():
    Germany().export()
