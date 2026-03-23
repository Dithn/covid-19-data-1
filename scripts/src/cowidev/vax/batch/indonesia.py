import requests

import pandas as pd
from tableauscraper import TableauScraper as TS

from cowidev.vax.utils.utils import build_vaccine_timeline
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.files import load_data


class Indonesia(CountryVaxBase):
    location = "Indonesia"
    source_url_ref = "https://data.covid19.go.id/public/index.html"
    source_url = "https://data.covid19.go.id/public/api/pemeriksaan-vaksinasi.json"

    def read(self) -> pd.DataFrame:
        data = requests.get(self.source_url).json()
        assert set(data["vaksinasi"]["harian"][-1].keys()) == {
            "key_as_string",
            "key",
            "doc_count",
            "jumlah_vaksinasi_2",
            "jumlah_vaksinasi_1",
            "jumlah_jumlah_vaksinasi_1_kum",
            "jumlah_jumlah_vaksinasi_2_kum",
        }, f'New columns found! Check {data["vaksinasi"]["harian"][-1].keys()}'
        records = [
            {
                "date": record["key_as_string"],
                "dose_1": record["jumlah_jumlah_vaksinasi_1_kum"]["value"],
                "dose_2": record["jumlah_jumlah_vaksinasi_2_kum"]["value"],
            }
            for record in data["vaksinasi"]["harian"]
        ]
        df = pd.DataFrame(records)
        return df

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(location=self.location, source_url=self.source_url_ref)

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(
            build_vaccine_timeline,
            {
                "Sinovac": "2020-12-01",
                "Oxford/AstraZeneca": "2021-03-22",
                "Sinopharm/Beijing": "2021-05-18",
                "Moderna": "2021-07-17",
                "Pfizer/BioNTech": "2021-08-29",
                "Johnson&Johnson": "2021-09-11",
                "Novavax": "2021-11-27",
            },
        )

    def pipe_merge_legacy(self, df: pd.DataFrame) -> pd.DataFrame:
        df_legacy = load_data(f"{self.location.lower()}-legacy")
        # df_legacy = df_legacy[~df_legacy.date.isin(df.date)]
        df = df[df.date > (df_legacy.date.max())]
        return pd.concat([df, df_legacy]).sort_values("date")

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.assign(
            people_vaccinated=df["dose_1"],
            total_vaccinations=df["dose_1"] + df["dose_2"],
            # single-shot data is missing, but the proportion of
            # J&J is very small, so it's an acceptable approximation
            # (see https://github.com/owid/covid-19-data/issues/2323#issuecomment-1031114133)
            people_fully_vaccinated=df["dose_2"],
        )
        df.loc[df.date >= "2022-01-01", "total_vaccinations"] = pd.NA  # booster data missing
        return df

    def pipe_add_latest_boosters(self, df: pd.DataFrame) -> pd.DataFrame:
        ts = TS()

        ts.loads("https://public.tableau.com/views/DashboardVaksinKemkes/TotalVaksinasiDosis1")
        first_doses = ts.getWorkbook().worksheets[0].data["SUM(Divaksin 1)-alias"].values[0]

        ts.loads("https://public.tableau.com/views/DashboardVaksinKemkes/TotalVaksinasiDosis2")
        second_doses = ts.getWorkbook().worksheets[0].data["SUM(Divaksin 2)-alias"].values[0]

        ts.loads("https://public.tableau.com/views/DashboardVaksinKemkes/TotalVaksinasiDosis3")
        boosters = ts.getWorkbook().worksheets[0].data["SUM(Divaksin 3)-alias"].values[0]

        df.loc[df.date == df.date.max(), "total_boosters"] = boosters
        df.loc[df.date == df.date.max(), "total_vaccinations"] = first_doses + second_doses + boosters
        return df

    def pipe_merge_current(self, df: pd.DataFrame, df_current: pd.DataFrame) -> pd.DataFrame:
        df = df.merge(df_current, on="date", how="left")
        df = df.assign(
            total_vaccinations=df.total_vaccinations.fillna(df.total_vaccinations_current),
            total_boosters=df.total_boosters.fillna(df.total_boosters_current),
        )
        return df

    def pipeline(self, df: pd.DataFrame, df_current: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_metadata)
            .pipe(self.pipe_metrics)
            .pipe(self.pipe_add_latest_boosters)
            .pipe(self.make_monotonic)
            .pipe(self.pipe_merge_legacy)
            .pipe(self.pipe_merge_current, df_current)
            .pipe(self.pipe_vaccine)[
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
        )

    def read_current(self):
        return pd.read_csv(self.output_path, usecols=["date", "total_boosters", "total_vaccinations"]).rename(
            columns={"total_boosters": "total_boosters_current", "total_vaccinations": "total_vaccinations_current"}
        )

    def export(self):
        # Read current
        df_current = self.read_current()
        df = self.read().pipe(self.pipeline, df_current)
        df.to_csv(self.output_path, index=False)


def main():
    Indonesia().export()
