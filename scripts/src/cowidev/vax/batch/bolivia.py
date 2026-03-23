import pandas as pd

from cowidev.vax.utils.utils import build_vaccine_timeline, make_monotonic
from cowidev.vax.utils.base import CountryVaxBase


class Bolivia(CountryVaxBase):
    location: str = "Bolivia"
    source_url: list = {
        "doses_unique": "https://github.com/dquintani/vacunacion/raw/main/datos/unicas_acumulado.csv",
        "doses_1": "https://github.com/dquintani/vacunacion/raw/main/datos/primeras_bidosis_acumulado.csv",
        "doses_2": "https://github.com/dquintani/vacunacion/raw/main/datos/segundas_bidosis_acumulado.csv ",
        "doses_boosters_1": "https://github.com/dquintani/vacunacion/raw/main/datos/dosis_refuerzo1_acumulado.csv",
    }
    source_url_ref: str = "https://github.com/dquintani/vacunacion/"

    def read(self):
        df = None
        for metric, url in self.source_url.items():
            column_rename = {"Unnamed: 0": "date", "Bolivia": metric}
            df_ = pd.read_csv(url, usecols=column_rename.keys()).rename(columns=column_rename)
            if df is None:
                df = df_
            else:
                df = df.merge(df_, on="date")
        return df

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(
            people_vaccinated=df.doses_1 + df.doses_unique,
            people_fully_vaccinated=df.doses_2 + df.doses_unique,
            total_boosters=df.doses_boosters_1,
            total_vaccinations=df.doses_1 + df.doses_2 + df.doses_unique + df.doses_boosters_1,
        ).drop(columns=self.source_url.keys())

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(
            location=self.location,
            source_url=self.source_url_ref,
        )

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        return build_vaccine_timeline(
            df,
            {
                "Sputnik V": "2021-01-01",
                "Oxford/AstraZeneca": "2021-04-04",
                "Sinopharm/Beijing": "2021-04-04",
                "Pfizer/BioNTech": "2021-05-04",
                "Johnson&Johnson": "2021-08-24",
            },
        )

    def pipe_columns_out(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[
            [
                "location",
                "date",
                "vaccine",
                "source_url",
                "people_vaccinated",
                "people_fully_vaccinated",
                "total_boosters",
                "total_vaccinations",
            ]
        ]

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_metrics)
            .pipe(self.pipe_metadata)
            .pipe(self.pipe_vaccine)
            .pipe(self.pipe_columns_out)
            .pipe(make_monotonic, max_removed_rows=15)
        )

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Bolivia().export()
