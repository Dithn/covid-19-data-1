import requests

import pandas as pd

from cowidev.utils.clean import clean_date_series
from cowidev.utils.utils import check_known_columns
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.utils import build_vaccine_timeline


class Greece(CountryVaxBase):
    location = "Greece"
    source_url = "https://www.data.gov.gr/api/v1/query/mdg_emvolio?date_from=2020-12-28"
    source_url_ref = "https://www.data.gov.gr/datasets/mdg_emvolio/"
    token = "b1ef5949bebace574a0d7e58b5cdf4018353121e"

    def read(self) -> pd.DataFrame:
        data = requests.get(self.source_url, headers={"Authorization": f"Token {self.token}"}).json()
        df = pd.DataFrame.from_records(data)
        check_known_columns(
            df,
            [
                "area",
                "areaid",
                "dailydose1",
                "dailydose2",
                "dailydose3",
                "daydiff",
                "daytotal",
                "referencedate",
                "totaldistinctpersons",
                "totaldose1",
                "totaldose2",
                "totaldose3",
                "totalvaccinations",
            ],
        )
        return (
            df.rename(
                columns={
                    "referencedate": "date",
                    "totaldistinctpersons": "people_vaccinated",
                    "totaldose2": "people_fully_vaccinated",
                    "totaldose3": "total_boosters",
                    "totalvaccinations": "total_vaccinations",
                }
            )[["people_vaccinated", "people_fully_vaccinated", "total_boosters", "total_vaccinations", "date"]]
            .groupby("date")
            .sum()
            .reset_index()
        )

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(date=clean_date_series(df.date, "%Y-%m-%dT%H:%M:%S"))

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(
            location=self.location,
            source_url=self.source_url_ref,
        )

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        return build_vaccine_timeline(
            df,
            {
                "Pfizer/BioNTech": "2020-12-01",
                "Moderna": "2021-01-13",
                "Oxford/AstraZeneca": "2021-02-10",
                "Johnson&Johnson": "2021-04-28",
                "Novavax": "2022-03-02", # Source: https://covid19.who.int/
            },
        )

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_metadata).pipe(self.pipe_vaccine).pipe(self.pipe_date)

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Greece().export()
