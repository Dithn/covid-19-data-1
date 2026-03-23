import pandas as pd

from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.utils import build_vaccine_timeline

vaccine_mapping = {
    "BBIBP-CorV(Sinopharm)": "Sinopharm/Beijing",
    "Comirnaty": "Pfizer/BioNTech",
    "CoronaVac(Sinovac)": "Sinovac",
    "Covishield(ChAdOx1_nCoV-19)": "Oxford/AstraZeneca",
    "Jcovden": "Johnson&Johnson",
    "Nuvaxovid": "Novavax",
    "Spikevax": "Moderna",
    "Vaxzevria": "Oxford/AstraZeneca",
}
one_dose_vaccines = ["Johnson&Johnson"]


class Latvia(CountryVaxBase):
    location = "Latvia"
    source_page = "https://data.gov.lv/dati/eng/dataset/covid19-vakcinacijas"
    source_url_1 = "https://data.gov.lv/dati/datastore/dump/51725018-49f3-40d1-9280-2b13219e026f"
    source_url_2 = "https://data.gov.lv/dati/datastore/dump/9320d913-a4a2-4172-b521-73e58c2cfe83"

    def _read_one(self, url: str):
        return pd.read_csv(
            url,
            usecols=[
                "Vakcinācijas datums",
                "Vakcinēto personu skaits",
                "Vakcinācijas posms",
                "Preparāts",
            ],
        )

    def read(self):
        df_1 = self._read_one(self.source_url_1)
        df_2 = self._read_one(self.source_url_2)
        return pd.concat([df_1, df_2], ignore_index=True)

    def pipe_base(self, df: pd.DataFrame) -> pd.DataFrame:
        df["Vakcinācijas datums"] = df["Vakcinācijas datums"].str.slice(0, 10)
        df["vaccine"] = df["Preparāts"].str.strip()
        vaccines_wrong = set(df["vaccine"].unique()).difference(set(vaccine_mapping) | {"Ambirix"})
        if vaccines_wrong:
            raise ValueError(f"Missing vaccines: {vaccines_wrong}")
        df = df[~df.vaccine.isin(["Ambirix"])]
        return (
            df.replace(vaccine_mapping)
            .drop(columns=["Preparāts"])
            .replace(
                {
                    "1.pote": "people_vaccinated",
                    "2.pote": "people_fully_vaccinated",
                    "3.pote": "dose_3",
                    "1.balstvakcinācija": "booster_1",
                    "2.balstvakcinācija": "booster_2",
                }
            )
        )

    def pipe_pivot(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.copy()
            .rename(columns={"Vakcinācijas datums": "date"})
            .groupby(["date", "Vakcinācijas posms", "vaccine"], as_index=False)
            .sum()
            .pivot(
                index=["date", "vaccine"],
                columns="Vakcinācijas posms",
                values="Vakcinēto personu skaits",
            )
            .reset_index()
            .sort_values("date")
        )

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df["total_vaccinations"] = (
            df["people_vaccinated"].fillna(0)
            + df["people_fully_vaccinated"].fillna(0)
            + df["dose_3"].fillna(0)
            + df["booster_1"].fillna(0)
            + df["booster_2"].fillna(0)
        )
        df["total_boosters"] = df["dose_3"].fillna(0) + df["booster_1"].fillna(0) + df["booster_2"].fillna(0)
        df.loc[df["vaccine"].isin(one_dose_vaccines), "people_fully_vaccinated"] = df.people_vaccinated
        return df

    def _remove_vaccines(self, df, approval_timeline):
        vax_amount = df[["vaccine", "total_vaccinations"]].groupby("vaccine").sum()
        vax_amount = vax_amount.where(lambda x: x < 100).dropna()
        for v in vax_amount.index:
            approval_timeline.pop(v, None)  # It has never been approved in Latvia
        return approval_timeline

    def pipe_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df[df.date >= "2020-12-01"]
        approval_timeline = df[["vaccine", "date"]].groupby("vaccine").min().to_dict()["date"]
        approval_timeline = self._remove_vaccines(df, approval_timeline)
        return (
            df.groupby("date", as_index=False)
            .agg(
                {
                    "total_vaccinations": "sum",
                    "people_vaccinated": "sum",
                    "people_fully_vaccinated": "sum",
                    "total_boosters": "sum",
                }
            )
            .pipe(build_vaccine_timeline, approval_timeline)
        )

    def pipe_cumsum(self, df: pd.DataFrame) -> pd.DataFrame:
        df[["total_vaccinations", "people_vaccinated", "people_fully_vaccinated", "total_boosters"]] = df[
            ["total_vaccinations", "people_vaccinated", "people_fully_vaccinated", "total_boosters"]
        ].cumsum()
        return df

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(location=self.location, source_url=self.source_page)

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_pivot)
            .pipe(self.pipe_metrics)
            .pipe(self.pipe_aggregate)
            .pipe(self.pipe_cumsum)
            .pipe(self.pipe_metadata)[
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
        )

    def pipeline_manufacturer(self, df: pd.DataFrame) -> pd.DataFrame:
        df = (
            df.rename(
                columns={
                    "Vakcinācijas datums": "date",
                    "Vakcinēto personu skaits": "total_vaccinations",
                }
            )
            .groupby(["date", "vaccine"], as_index=False)["total_vaccinations"]
            .sum()
            .sort_values("date")
        )
        df = df.assign(
            total_vaccinations=df.groupby("vaccine", as_index=False)["total_vaccinations"].cumsum(),
            location=self.location,
        )[["location", "date", "vaccine", "total_vaccinations"]].sort_values(["date", "vaccine"])
        return df

    def export(self):
        # logger.info("read")
        # df = self.read()
        df = self.from_ice()  # temporary
        df_base = df.pipe(self.pipe_base)

        # Main data
        df = df_base.pipe(self.pipeline)
        # Manufacturer data
        df_man = df_base.pipe(self.pipeline_manufacturer)
        # Export
        self.export_datafile(
            df,
            df_manufacturer=df_man,
            meta_manufacturer={"source_name": "National Health Service", "source_url": self.source_page},
        )


def main():
    Latvia().export()
