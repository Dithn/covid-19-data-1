import io
import os
import tempfile
import zipfile

import pandas as pd
import requests

from cowidev.utils import clean_date_series
from cowidev.utils.utils import check_known_columns
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.utils import build_vaccine_timeline, make_monotonic


class Singapore(CountryVaxBase):
    def __init__(self):
        self.location = "Singapore"
        self.source_url = "https://storage.data.gov.sg/covid-19-vaccination/covid-19-vaccination.zip"
        self.source_url_ref = "https://data.gov.sg/dataset/covid-19-vaccination"
        self.vaccine_timeline = {
            "Pfizer/BioNTech": "2020-12-01",
            "Moderna": "2021-03-15",
            "Sinovac": "2021-06-28",
            "Sinopharm/Beijing": "2021-12-03",
            "Novavax": "2022-05-18",
        }

    def read(self) -> str:
        with tempfile.TemporaryDirectory() as tf:
            r = requests.get(self.source_url)
            z = zipfile.ZipFile(io.BytesIO(r.content))
            z.extractall(tf)

            df_primary = pd.read_csv(os.path.join(tf, "progress-of-covid-19-vaccination.csv"))
            check_known_columns(
                df_primary,
                [
                    "vacc_date",
                    "received_at_least_one_dose",
                    "full_regimen",
                    "received_one_dose_pcttakeup",
                    "full_regimen_pcttakeup",
                    "minimum_protection_pcttakeup",
                    "minimum_protection",
                ],
            )

            # df_boosters = pd.read_csv(os.path.join(tf, "progress-of-vaccine-booster-programme.csv"))
            # check_known_columns(
            #     df_boosters,
            #     [
            #         "vacc_date",
            #         "received_booster_or_three_doses",
            #         "received_booster_or_three_doses_pcttakeup",
            #     ],
            # )
        # df = self._merge_primary_and_boosters(df_primary, df_boosters)

        df_primary["vacc_date"] = clean_date_series(df_primary.vacc_date, "%Y-%m-%d")
        df = df_primary.drop_duplicates(subset=["vacc_date"], keep=False)
        return df

    def _merge_primary_and_boosters(self, df_primary, df_boosters):
        if not df_boosters.vacc_date.str.match(r"\d{4}-\d{2}-\d{2}").all():
            try:
                df_boosters["vacc_date"] = clean_date_series(df_boosters.vacc_date, "%d-%b-%y")
            except:
                try:
                    df_boosters["vacc_date"] = clean_date_series(df_boosters.vacc_date, "%d/%m/%Y")
                except:
                    df_boosters["vacc_date"] = clean_date_series(df_boosters.vacc_date, "%d%b%Y")
            df_boosters = df_boosters.drop_duplicates(subset=["vacc_date"], keep=False)
        if not df_primary.vacc_date.str.match(r"\d{4}-\d{2}-\d{2}").all():
            try:
                df_primary["vacc_date"] = clean_date_series(df_primary.vacc_date, "%d-%b-%y")
            except:
                df_primary["vacc_date"] = clean_date_series(df_primary.vacc_date, "%d/%m/%Y")
            df_primary = df_primary.drop_duplicates(subset=["vacc_date"], keep=False)
        df = pd.merge(df_primary, df_boosters, on="vacc_date", how="outer", validate="one_to_one")
        return df

    def pipe_rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(
            columns={
                "vacc_date": "date",
                "received_at_least_one_dose": "people_vaccinated",
                "full_regimen": "people_fully_vaccinated",
                # "received_booster_or_three_doses": "total_boosters",
            }
        )[
            [
                "date",
                "people_vaccinated",
                "people_fully_vaccinated",
                # "total_boosters",
            ]
        ]

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        # df.loc[df.date < "2022-01-01", "total_boosters"] = df.loc[df.date < "2022-01-01", "total_boosters"].fillna(0)
        return df.assign(
            total_vaccinations=pd.NA
            # total_vaccinations=df.people_vaccinated.fillna(0)
            # + df.people_fully_vaccinated.fillna(0)
            # + df.total_boosters
        )

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(location=self.location, source_url=self.source_url_ref).pipe(
            build_vaccine_timeline, self.vaccine_timeline
        )

    def pipe_filter_dp(self, df: pd.DataFrame) -> pd.DataFrame:
        date_ex = ["2022-02-14"]
        df = df[~df.date.isin(date_ex)]
        return df

    def pipe_filter_timeseries(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df.date > "2022-10-25"]

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_metrics)
            .pipe(self.pipe_metadata)
            # .pipe(self.pipe_filter_dp)
            # .pipe(self.pipe_filter_timeseries)
            .pipe(make_monotonic, max_removed_rows=20)
        )

    def export(self):
        df = self.read().pipe(self.pipeline)
        # merge
        df_current = self.load_datafile()
        df = df.merge(df_current, on=["location", "date"], how="outer", suffixes=("", "_old"))
        df = df.assign(
            total_vaccinations=df.total_vaccinations_old,
            total_boosters=df.total_boosters,
        )
        self.export_datafile(df, valid_cols_only=True)


def main():
    Singapore().export()
