import pandas as pd

from cowidev.utils.utils import check_known_columns
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.utils import build_vaccine_timeline


class Belgium(CountryVaxBase):
    def __init__(self) -> None:
        self.location = "Belgium"
        self.source_url = "https://epistat.sciensano.be/Data/COVID19BE_VACC_STATUS.csv"
        self.source_url_vax1 = "https://epistat.sciensano.be/Data/COVID19BE_VACC.csv"
        self.source_url_ref = "https://epistat.wiv-isp.be/covid/"

    def export(self):
        # Read former data, to obtain number of people vaccinated (only until Oct 2023)
        # This dataset contains granular data at dose-level, but it ends in late 2023.
        # We also use early numbers on total number of vaccinations from it
        df_old = self.read_old().pipe(self.pipeline_old)

        # Read new data, which provides the remaining indicators
        # - With some workarounds, we can get estimates on booster doses, people vaccinated and total vaccinations.
        # - Howver, for the number of vaccinations, the initial values are a bit off, because the dataset lacks data on partly vaccinated people (only reports data once they are fully vaccinated).
        df_new = self.read_new().pipe(self.pipeline_new)

        # Combine both dataframes:
        df = self.combine_dfs(df_old, df_new)

        # Export
        self.export_datafile(df)

    def read_new(self) -> pd.DataFrame:
        df = pd.read_csv(self.source_url)
        check_known_columns(df, ["CAMPAIGN", "DATE", "REGION", "AGEGROUP", "SEX", "BRAND", "STATUS", "COUNT"])
        return df[["DATE", "STATUS", "BRAND", "COUNT"]]

    def read_old(self) -> pd.DataFrame:
        df = pd.read_csv(self.source_url_vax1)
        check_known_columns(df, ["DATE", "REGION", "AGEGROUP", "SEX", "BRAND", "DOSE", "COUNT"])
        return df[["DATE", "DOSE", "COUNT"]]

    def pipeline_old(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_dose_check)
            .pipe(self.pipe_aggregate)
            .pipe(self.pipe_rename_columns)
            .pipe(self.pipe_add_totals)
            .pipe(self.pipe_cumsum)
        )

    def pipeline_new(self, df: pd.DataFrame) -> pd.DataFrame:
        # Sanity checks
        assert set(df["STATUS"]) == {"Vaccinated", "Revaccinated"}, "Unknown status!"
        # Get number of doses
        msk = (df["BRAND"] != "Johnson&Johnson") & (df["STATUS"] == "Vaccinated")
        df["NUM_DOSES"] = df["COUNT"]
        df.loc[msk, "NUM_DOSES"] *= 2
        # Get people vaccinated, and number of boosters
        df_1 = df.groupby(["DATE", "STATUS"], as_index=False)[["COUNT"]].sum()
        df_1 = df_1.pivot(index="DATE", columns="STATUS", values="COUNT").fillna(0)
        df_1 = df_1.reset_index()
        df_1 = df_1.rename(columns={
            "DATE": "date",
            "Revaccinated": "total_boosters",
            "Vaccinated": "people_fully_vaccinated",
        })
        # Get total number of doses
        df_2 = df.groupby(["DATE"], as_index=False)[["NUM_DOSES"]].sum()
        df_2 = df_2.rename(columns={
            "DATE": "date",
            "NUM_DOSES": "total_vaccinations",
        })
        # Combine
        df = df_1.merge(df_2, on="date", how="outer")
        # Cum sum
        df = df.assign(
            total_vaccinations=df["total_vaccinations"].cumsum().astype(int),
            people_fully_vaccinated=df["people_fully_vaccinated"].cumsum().astype(int),
            total_boosters=df["total_boosters"].cumsum().astype(int),
        )
        return df

    def combine_dfs(self, df_old: pd.DataFrame, df_new: pd.DataFrame) -> pd.DataFrame:
        # Get relevant columns
        df_old = df_old[["date", "total_vaccinations", "people_vaccinated"]].rename(columns={
            "total_vaccinations": "total_vaccinations_old",
        })

        # Merge dataframes
        df = df_new.merge(df_old, on="date", how="outer").sort_values("date")

        # Get date when total_vaccinations starts being roughly similar between df_old and df_new
        diff = (df["total_vaccinations_old"] - df["total_vaccinations"]).abs() / df["total_vaccinations"]
        dt = df.loc[diff < 0.005, "date"].min()
        assert dt == "2022-01-05", "Check date!"
        msk = df["date"] < dt
        df.loc[msk, "total_vaccinations"] = df.loc[msk, "total_vaccinations_old"]

        # Drop columns
        df = df.drop(columns=["total_vaccinations_old"])

        # Add missing columns
        df = (
            df.pipe(self.pipe_vaccine_name)
            .pipe(self.pipe_metadata)
        )
        return df


    def pipe_dose_check(self, df: pd.DataFrame) -> pd.DataFrame:
        doses_wrong = set(df.DOSE).difference(["A", "B", "C", "E", "E2", "E3", "E4+"])
        if doses_wrong:
            raise ValueError(f"Invalid dose type {doses_wrong}")
        return df

    def pipe_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.groupby(["DATE", "DOSE"], as_index=False)
            .sum()
            .sort_values("DATE")
            .pivot(index="DATE", columns="DOSE", values="COUNT")
            .reset_index()
            .fillna(0)
        )

    def pipe_rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(
            columns={
                "DATE": "date",
            }
        )

    def pipe_add_totals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.assign(
            total_vaccinations=df.A + df.B + df.C + df.E + df.E2 + df.E3 + df["E4+"],
            people_vaccinated=df.A + df.C,
            people_fully_vaccinated=df.B + df.C,
            total_boosters=df.E + df.E2 + df.E3 + df["E4+"],
        )
        return df.drop(columns=["A", "B", "C", "E"])

    def pipe_cumsum(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(
            total_vaccinations=df.total_vaccinations.cumsum().astype(int),
            people_vaccinated=df.people_vaccinated.cumsum().astype(int),
            people_fully_vaccinated=df.people_fully_vaccinated.cumsum().astype(int),
            total_boosters=df.total_boosters.cumsum().astype(int),
        )

    def pipe_vaccine_name(self, df: pd.DataFrame) -> pd.DataFrame:
        # Source:
        # https://datastudio.google.com/embed/u/0/reporting/c14a5cfc-cab7-4812-848c-0369173148ab/page/p_j1f02pfnpc
        return build_vaccine_timeline(
            df,
            {
                "Pfizer/BioNTech": "2020-12-28",
                "Moderna": "2021-01-11",
                "Oxford/AstraZeneca": "2021-02-12",
                "Johnson&Johnson": "2021-04-28",
                "Novavax": "2022-01-19",
            },
        )

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(location=self.location, source_url=self.source_url_ref)


def main():
    Belgium().export()
