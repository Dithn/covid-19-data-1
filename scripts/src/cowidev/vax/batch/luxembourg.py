import pandas as pd

from cowidev.utils.utils import check_known_columns
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.utils import add_latest_who_values, build_vaccine_timeline


class Luxembourg(CountryVaxBase):
    location = "Luxembourg"
    source_url = "https://data.public.lu/en/datasets/r/af7cd843-dfe5-440a-9ab2-d22ffef8844c"
    source_url_ref = "https://data.public.lu/en/datasets/donnees-covid19/#_"

    def read(self) -> pd.DataFrame:
        df = pd.read_excel(self.source_url)
        check_known_columns(
            df,
            [
                "Date",
                "Nombre de dose 1",
                "Nombre de dose 2",
                "Nombre de Dose complémentaire par rapport à schéma complet",
                "Nombre total de doses",
            ],
        )
        return df

    def pipe_rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(
            columns={
                "Date": "date",
                "Nombre de dose 1": "people_vaccinated",
                "Nombre de dose 2": "people_fully_vaccinated",
                "Nombre de Dose complémentaire par rapport à schéma complet": "total_boosters",
                "Nombre total de doses": "total_vaccinations",
            }
        )

    def pipe_correct_time_series(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Since 2021-04-14 Luxembourg is using J&J, therefore dose2 == people_fully_vaccinated no longer
        works. As a temporary fix while they report the necessary data, we're inserting one PDF report
        to avoid showing an old value for people_fully_vaccinated in dashboard that re-use our latest
        totals without showing how old they are.
        The publisher was contacted on 2021-O9-21 https://twitter.com/redouad/status/1439992459166158857
        """
        df.loc[df.date >= "2021-04-14", "people_fully_vaccinated"] = pd.NA
        df = add_latest_who_values(df, "Luxembourg", ["people_fully_vaccinated"])
        return df

    def pipe_running_totals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.sort_values("date")
        df[["people_vaccinated", "people_fully_vaccinated", "total_boosters", "total_vaccinations"]] = df[
            ["people_vaccinated", "people_fully_vaccinated", "total_boosters", "total_vaccinations"]
        ].cumsum()
        return df

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(source_url=self.source_url_ref, location="Luxembourg")

    def pipe_vaccines(self, df: pd.DataFrame) -> pd.DataFrame:
        return build_vaccine_timeline(
            df,
            {
                "Pfizer/BioNTech": "2020-12-01",
                "Moderna": "2021-01-20",
                "Oxford/AstraZeneca": "2021-02-10",
                "Johnson&Johnson": "2021-04-14",
                # Source: https://www.ecdc.europa.eu/en/publications-data/data-covid-19-vaccination-eu-eea
                "Novavax": "2022-03-04",
            },
        )

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_running_totals)
            .pipe(self.pipe_metadata)
            .pipe(self.pipe_correct_time_series)
            .pipe(self.pipe_vaccines)
        )

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Luxembourg().export()
