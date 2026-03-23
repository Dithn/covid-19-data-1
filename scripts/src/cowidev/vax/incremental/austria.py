import pandas as pd

from cowidev.utils.utils import check_known_columns
from cowidev.utils.web.download import read_csv_from_url
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.utils.clean import clean_date_series
from cowidev.vax.utils.incremental import increment


class Austria(CountryVaxBase):
    location: str = "Austria"
    source_url: str = "https://info.gesundheitsministerium.gv.at/data/COVID19_vaccination_municipalities_v202210.csv"
    source_url_ref: str = "https://www.data.gv.at/katalog/dataset/519d4c3d-142b-448f-b83a-d32c65dd7c94#resources"

    def read(self) -> pd.DataFrame:
        df = read_csv_from_url(self.source_url, sep=";", ciphers_low=True)
        check_known_columns(
            df,
            [
                "date",
                "municipality_id",
                "municipality_name",
                "municipality_population",
                "vaccination_1",
                "vaccination_2",
                "vaccination_3",
                "vaccination_4+",
            ],
        )
        assert df["date"].nunique() == 1, "More than one date detected!"

        return df[["date", "vaccination_1", "vaccination_2", "vaccination_3", "vaccination_4+"]]

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        df["date"] = clean_date_series(df["date"], "%Y-%m-%dT%H:%M:%S%z")
        return df

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        # Total vaccinations
        df.loc[:, "total_vaccinations"] = (
            df["vaccination_1"] + df["vaccination_2"] + df["vaccination_3"] + df["vaccination_4+"]
        )
        # People vaccinated
        df.loc[:, "people_vaccinated"] = df["vaccination_1"]
        # People fully vaccinated
        df.loc[:, "people_fully_vaccinated"] = df["vaccination_2"]
        # Total boosters
        df.loc[:, "total_boosters"] = df["vaccination_3"] + df["vaccination_4+"]

        return (
            df[
                [
                    "date",
                    "people_vaccinated",
                    "people_fully_vaccinated",
                    "total_vaccinations",
                    "total_boosters",
                ]
            ]
            .groupby("date", as_index=False)
            .sum()
        )

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(
            location=self.location,
            source_url=self.source_url,
        )

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        df["vaccine"] = "Johnson&Johnson, Moderna, Novavax, Oxford/AstraZeneca, Pfizer/BioNTech"
        return df

    def pipe_to_series(self, df: pd.DataFrame) -> pd.DataFrame:
        assert len(df) == 1, "More than row!"
        return df.iloc[0]

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_date)
            .pipe(self.pipe_metrics)
            .pipe(self.pipe_metadata)
            .pipe(self.pipe_vaccine)
            .pipe(self.pipe_to_series)
        )

    def export(self):
        data = self.read().pipe(self.pipeline)
        print(data)
        increment(
            location=data["location"],
            total_vaccinations=data["total_vaccinations"],
            people_vaccinated=data["people_vaccinated"],
            people_fully_vaccinated=data["people_fully_vaccinated"],
            date=data["date"],
            source_url=data["source_url"],
            vaccine=data["vaccine"],
            total_boosters=data["total_boosters"],
        )


def main():
    Austria().export()
