import io
import requests

import numpy as np
import pandas as pd

from cowidev.utils.utils import check_known_columns
from cowidev.vax.utils.utils import build_vaccine_timeline
from cowidev.vax.utils.base import CountryVaxBase


class HongKong(CountryVaxBase):
    location: str = "Hong Kong"
    source_url: str = "https://www.fhb.gov.hk/download/opendata/COVID19/vaccination-rates-over-time-by-age.csv"
    source_url_ref: str = "https://data.gov.hk/en-data/dataset/hk-dh-chpsebcddr-novel-infectious-agent"
    vaccine_mapping: dict = {
        "Sinovac": "Sinovac",
        "BioNTech": "Pfizer/BioNTech",
    }
    age_valid = {
        "0-11": "0-19",
        "12-19": "0-19",
        "20-29": "20-29",
        "30-39": "30-39",
        "40-49": "40-49",
        "50-59": "50-59",
        "60-69": "60-69",
        "70-79": "70-79",
        "80 and above": "80-",
    }
    vaccines_valid = ["Sinovac", "BioNTech"]

    def read(self) -> pd.DataFrame:
        response = requests.get(self.source_url).content
        df = pd.read_csv(io.StringIO(response.decode("utf-8")))
        check_known_columns(
            df,
            [
                "Date",
                "Age Group",
                "Sex",
                "Sinovac 1st dose",
                "Sinovac 2nd dose",
                "Sinovac 3rd dose",
                "Sinovac 4th dose",
                "Sinovac 5th dose",
                "Sinovac 6th dose",
                'Sinovac 7th dose',
                "BioNTech 1st dose",
                "BioNTech 2nd dose",
                "BioNTech 3rd dose",
                "BioNTech 4th dose",
                "BioNTech 5th dose",
                "BioNTech 6th dose",
                'BioNTech 7th dose',
            ],
        )
        return df

    def pipe_reshape(self, df: pd.DataFrame) -> pd.DataFrame:
        df = (
            df.rename(columns={"Date": "date", "Age Group": "age_group"})
            .drop(columns=["Sex"])
            .melt(id_vars=["date", "age_group"], value_name="total_vaccinations")
            .groupby(["date", "age_group", "variable"], as_index=False)
            .sum()
        )
        df[["vaccine", "dose"]] = df.variable.str.extract(r"^(\w+) (.*)$")
        df = df.drop(columns="variable").sort_values("date")
        df["total_vaccinations"] = df.groupby(["vaccine", "dose", "age_group"]).cumsum()
        return df

    def pipe_add_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(location=self.location, source_url=self.source_url_ref)

    def pipeline_base(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_reshape)

    def pipe_calculate_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df = (
            df.replace(
                {
                    "1st dose": "people_vaccinated",
                    "2nd dose": "people_fully_vaccinated",
                    "3rd dose": "total_boosters",
                    "4th dose": "total_boosters",
                    "5th dose": "total_boosters",
                    "6th dose": "total_boosters",
                }
            )
            .groupby(["date", "dose"], as_index=False)
            .sum()
            .pivot(index="date", columns="dose", values="total_vaccinations")
            .reset_index()
        )
        df["total_vaccinations"] = df.people_vaccinated + df.people_fully_vaccinated + df.total_boosters
        return df

    def pipe_add_vaccines(self, df: pd.DataFrame) -> pd.DataFrame:
        return build_vaccine_timeline(
            df,
            {
                "Sinovac": "2021-02-22",
                "Pfizer/BioNTech": "2021-03-06",
            },
        )

    def pipe_filter_dp(self, df: pd.DataFrame) -> pd.DataFrame:
        dates_invalid = [
            "2021-10-13",
            "2022-02-01",
            "2023-01-22",
            "2023-01-23",
            "2023-07-16",
            "2023-06-11",
            "2023-06-22",
            "2023-06-25",
            "2023-06-27",
            "2023-07-01",
            "2023-07-02",
            "2023-07-04",
            "2023-07-09",
            "2023-07-16",
            "2023-07-17",
            "2023-07-18",
        ]
        # Since August 2023 there are tons of outliers
        value = df.loc[df["date"] == "2023-08-01", "total_vaccinations"].item()
        dates_additional = list(df.loc[(df["date"] >= "2023-08-01") & (df["total_vaccinations"] < value), "date"])
        dates_invalid += dates_additional
        msk = df.date.isin(dates_invalid)
        df = df[~msk]
        # df.loc[df["date"] == "2023-08-29", "total_boosters"] = np.nan
        return df

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_calculate_metrics)
            .pipe(self.pipe_add_vaccines)
            .pipe(self.pipe_add_metadata)
            .pipe(self.pipe_filter_dp)
            .pipe(self.make_monotonic)
        )

    def pipe_sum_manufacturer(self, df: pd.DataFrame) -> pd.DataFrame:
        assert set(df["vaccine"].unique()) == set(self.vaccine_mapping.keys())
        df = df.drop(columns="dose").replace(self.vaccine_mapping).groupby(["date", "vaccine"], as_index=False).sum()
        return df[df.total_vaccinations > 0]

    def pipeline_manufacturer(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_sum_manufacturer)
            .assign(location=self.location)
            .pipe(self.pipe_filter_manuf_dp)
            .pipe(self.make_monotonic, ["vaccine"])
        )

    def pipe_filter_manuf_dp(self, df):
        value_sin = df.loc[(df["date"] == "2023-08-01") & (df["vaccine"] == "Sinovac"), "total_vaccinations"].item()
        msk_sin = ((df.vaccine == "Sinovac") & (df.date.isin([
            "2021-10-13",
            "2022-01-31",
            "2023-01-22",
            "2023-01-23",
            "2023-06-11",
            "2023-06-22",
            "2023-06-25",
            "2023-06-27",
            "2023-07-01",
            "2023-07-02",
            "2023-07-04",
            "2023-07-09",
            "2023-07-16",
            "2023-07-17",
            "2023-07-18",
        ]) | ((df["date"] >= "2023-08-01") & (df["total_vaccinations"] < value_sin))))
        value_pfi = df.loc[(df["date"] == "2023-08-01") & (df["vaccine"] == "Pfizer/BioNTech"), "total_vaccinations"].item()
        msk_pfi = ((df.vaccine == "Pfizer/BioNTech") & (df.date.isin([
            "2021-10-13",
            "2022-02-01",
            "2023-01-22",
            "2023-01-23",
            "2023-06-11",
            "2023-06-22",
            "2023-06-25",
            "2023-06-27",
            "2023-07-01",
            "2023-07-02",
            "2023-07-04",
            "2023-07-09",
            "2023-07-16",
            "2023-07-17",
            "2023-07-18",
        ]
        ) | ((df["date"] >= "2023-08-01") & (df["total_vaccinations"] < value_pfi))))
        return df[~(msk_sin | msk_pfi)]

    def pipe_age_checks(self, df: pd.DataFrame):
        vax_wrong = set(df.vaccine).difference(self.vaccines_valid)
        if vax_wrong:
            raise ValueError(
                f"Can't extract age data. New vaccine(s) detected: {vax_wrong}. Generally it is OK unless single-dose"
                " vaccines are in use!"
            )
        age_wrong = set(df.age_group).difference(self.age_valid)
        if age_wrong:
            raise ValueError(f"Wrong age group(s): {age_wrong}")
        return df

    def pipe_age_agg(self, df: pd.DataFrame):
        df = df.assign(age_group=df.age_group.replace(self.age_valid))
        df = df.groupby(["date", "age_group", "dose"], as_index=False).sum()
        return df

    def pipe_age_groups(self, df: pd.DataFrame):
        df[["age_group_min", "age_group_max"]] = df.age_group.str.split("-", expand=True)
        return df

    def pipe_age_pivot(self, df: pd.DataFrame):
        return (
            df.pivot(index=["date", "age_group_min", "age_group_max"], columns="dose", values="total_vaccinations")
            .reset_index()
            .rename(
                columns={
                    "1st dose": "people_vaccinated",
                    "2nd dose": "people_fully_vaccinated",
                    "3rd dose": "people_with_booster",
                }
            )
        )

    def pipe_age_filter(self, df: pd.DataFrame):
        msk = (df.date == "2022-02-01") & (df.age_group_min == "0")
        return df[~msk]

    def pipeline_age(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_age_checks)
            .pipe(self.pipe_age_agg)
            .pipe(self.pipe_age_groups)
            .pipe(self.pipe_age_pivot)
            .pipe(self.pipe_age_per_capita)
            .pipe(self.pipe_age_filter)
            .assign(location=self.location)
        )

    def check_number_age_groups_latest(self, df: pd.DataFrame, raise_error: bool = False):
        """Check that there are 9 age groups in the 10 latest dates. If not, raise an error."""
        x = df.groupby("date").age_group.nunique()
        x = df.groupby("date").age_group.nunique()
        wrong_rows = x.tail(10)[x < 9]
        if wrong_rows.any():
            wrong_dates = wrong_rows.index.tolist()
            df = df[~df["date"].isin(wrong_dates)]
            if raise_error:
                raise ValueError(f"Missing age groups! Check dates {wrong_rows.index.tolist()}")
        # Ignore dates
        df = df[~df["date"].isin(["2023-01-21"])]
        return df

    def filter_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        DATES_FILTER = [
            "2023-05-21",
            "2023-06-04",
            "2023-07-23",
            "2023-07-29",
            "2023-07-30",
            "2023-08-06",
            "2023-08-07",
            "2023-08-09",
            "2023-08-13",
            "2023-08-14",
            "2023-08-15",
            "2023-08-17",
            "2023-08-18",
            "2023-08-20",
        ]
        df = df[~df["date"].isin(DATES_FILTER)]
        return df

    def export(self):
        df_base = self.read().pipe(self.pipeline_base)
        # Check on age groups
        df_base = self.check_number_age_groups_latest(df_base)
        # Filter date
        df_base = self.filter_dates(df_base)
        # Main data
        df = df_base.pipe(self.pipeline)
        # Manufacturer
        df_man = df_base.pipe(self.pipeline_manufacturer)
        # Age
        df_age = df_base.pipe(self.pipeline_age)
        # Export
        self.export_datafile(
            df,
            df_manufacturer=df_man,
            meta_manufacturer={"source_name": "Food and Health Bureau", "source_url": self.source_url_ref},
            df_age=df_age,
            meta_age={"source_name": "Food and Health Bureau", "source_url": self.source_url_ref},
        )


def main():
    HongKong().export()
