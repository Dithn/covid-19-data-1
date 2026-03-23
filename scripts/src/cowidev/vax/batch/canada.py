import numpy as np
import pandas as pd

from cowidev.utils.utils import check_known_columns
from cowidev.utils.web import request_json
from cowidev.utils.web.download import read_csv_from_url
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.checks import validate_vaccines
from cowidev.vax.utils.utils import build_vaccine_timeline


class Canada(CountryVaxBase):
    location: str = "Canada"
    source_name: str = "Public Health Agency of Canada"
    source_url: str = "https://api.covid19tracker.ca/reports"
    source_url_a: str = (
        "https://health-infobase.canada.ca/src/data/covidLive/vaccination-coverage-byAgeAndSex-overTimeDownload.csv"
    )
    source_url_m: str = (
        "https://health-infobase.canada.ca/src/data/covidLive/vaccination-administration-bydosenumber2.csv"
    )
    source_url_ref: str = "https://covid19tracker.ca/vaccinationtracker.html"
    source_url_age: str = "https://health-infobase.canada.ca/covid-19/vaccination-coverage/"
    source_url_man: str = "https://health-infobase.canada.ca/covid-19/vaccine-administration/"
    cols_age: dict = {
        "week_end": "date",
        "age": "age",
        "numtotal_atleast1dose": "people_vaccinated",
        "numtotal_fully": "people_fully_vaccinated",
        "numtotal_additional": "people_with_booster",
    }
    cols_man: dict = {
        "week_end": "date",
        "product_name": "vaccine",
        "numtotal_dose1_admin": "total_vaccinations",
        "numtotal_dose2_admin": "total_vaccinations",
        "numtotal_dose3_admin": "total_vaccinations",
        "numtotal_dose4_admin": "total_vaccinations",
        "numtotal_dose5+_admin": "total_vaccinations",
        "numtotal_dosenotreported_admin": "total_vaccinations",
    }
    age_pattern: str = r"0?(\d{1,2})(?:–0?(\d{1,2})|\+)"
    vaccine_mapping: dict = {
        "AstraZeneca Vaxzevria/COVISHIELD": "Oxford/AstraZeneca",
        "Janssen": "Johnson&Johnson",
        "Janssen Jcovden": "Johnson&Johnson",
        "Medicago Covifenz": "Medicago",
        "Moderna Spikevax": "Moderna",
        "Moderna Spikevax (ages 6 months-5 years)": "Moderna",
        "Moderna Spikevax Bivalent": "Moderna",
        "Moderna Spikevax Bivalent Original/BA1": "Moderna",
        "Not reported": None,
        "Novavax": "Novavax",
        "Novavax Nuvaxovid": "Novavax",
        "Pfizer-BioNTech Comirnaty": "Pfizer/BioNTech",
        "Pfizer-BioNTech Comirnaty pediatric 5-11 years": "Pfizer/BioNTech",
        "Pfizer-BioNTech Comirnaty (ages 5-11 years)": "Pfizer/BioNTech",
        "Pfizer-BioNTech Comirnaty (ages 12 years and older)": "Pfizer/BioNTech",
        "Pfizer-BioNTech Comirnaty Bivalent Original and BA4/BA5": "Pfizer/BioNTech",
        "Pfizer-BioNTech Comirnaty pediatric 6 months-4 years": "Pfizer/BioNTech",
        "Pfizer-BioNTech Comirnaty Bivalent Original and BA1": "Pfizer/BioNTech",
        "Total": None,
        "Unknown": None,
    }
    max_filtered_dates: int = 3
    max_removed_rows: int = 22

    def read(self) -> pd.DataFrame:
        data = request_json(self.source_url)
        df = pd.DataFrame.from_records(data["data"])
        check_known_columns(
            df,
            [
                "date",
                "change_cases",
                "change_fatalities",
                "change_tests",
                "change_hospitalizations",
                "change_criticals",
                "change_recoveries",
                "change_vaccinations",
                "change_vaccinated",
                "change_boosters_1",
                "change_boosters_2",
                "change_vaccines_distributed",
                "total_cases",
                "total_fatalities",
                "total_tests",
                "total_hospitalizations",
                "total_criticals",
                "total_recoveries",
                "total_vaccinations",
                "total_vaccinated",
                "total_boosters_1",
                "total_boosters_2",
                "total_vaccines_distributed",
            ],
        )
        return df[["date", "change_vaccinations", "change_vaccinated", "change_boosters_1", "change_boosters_2"]]

    def read_age(self) -> pd.DataFrame:
        df = read_csv_from_url(self.source_url_a)
        check_known_columns(
            df,
            [
                "pruid",
                "prename",
                "prfname",
                "week_end",
                "sex",
                "age",
                "numtotal_atleast1dose",
                "numtotal_partially",
                "numtotal_fully",
                "numtotal_additional",
                "numtotal_2nd_additional",
                "numtotal_recommended_vax",
                "numtotal_vax_interest",
                "proptotal_atleast1dose",
                "proptotal_partially",
                "proptotal_fully",
                "proptotal_additional",
                "proptotal_2nd_additional",
                "proptotal_recommended_vax",
                "proptotal_vax_interest",
            ],
        )
        return df

    def read_manufacturer(self) -> pd.DataFrame:
        df = read_csv_from_url(self.source_url_m)
        check_known_columns(
            df,
            [
                "week_end",
                "pruid",
                "prename",
                "prfname",
                "product_name",
                "numtotal_totaldoses_admin",
                "numtotal_dose1_admin",
                "numtotal_dose2_admin",
                "numtotal_dose3_admin",
                "numtotal_dose4_admin",
                "numtotal_dose5+_admin",
                "numtotal_dosenotreported_admin",
                "numdelta_dose1",
                "numdelta_dose2",
                "numdelta_dose3",
                "numdelta_dose4",
                "numdelta_dose5+",
                "numdelta_notreported",
                "num2weekdelta_dose1",
                "num2weekdelta_dose2",
                "num2weekdelta_dose3",
                "num2weekdelta_dose4",
                "num2weekdelta_dose5+",
                "num2weekdelta_notreported",
                "num4weekdelta_dose1",
                "num4weekdelta_dose2",
                "num4weekdelta_dose3",
                "num4weekdelta_dose4",
                "num4weekdelta_dose5+",
                "num4weekdelta_notreported",
            ],
        )
        return df

    def pipeline_age(self, df: pd.DataFrame) -> pd.DataFrame:
        # Filter rows & columns
        df = df[(df.pruid == 1) & (df.sex == "All sexes") & df.age.str.match(self.age_pattern)]
        df = df[self.cols_age.keys()].rename(columns=self.cols_age)
        # Filter unneeded age groups (likely bc they were deprecated by the source)
        df = df[~df.age.isin(["0–17", "70–74", "75–79"])]
        # Parse age groups
        df[["age_group_min", "age_group_max"]] = df.age.str.extract(self.age_pattern).fillna("")
        # Convert data types and calculate per capita metrics
        metrics = df.filter(like="people_").columns
        df[metrics] = df[metrics].astype("float").fillna(0)
        df = df.pipe(self.pipe_age_per_capita)
        df = df.assign(location=self.location)
        # Monotonic
        # df = df.pipe(self.make_monotonic, ["age_group_min", "age_group_max"])
        return df

    def pipeline_manufacturer(self, df: pd.DataFrame) -> pd.DataFrame:
        # Filter rows & columns
        df = df[df.pruid == 1].fillna(0)
        df = df[self.cols_man.keys()].rename(columns=self.cols_man)
        # Dtype
        df = df.astype({"total_vaccinations": float})
        # Calculate total vaccinations
        df = df.groupby(df.columns, axis=1).sum()
        # Check and map vaccine names
        validate_vaccines(df, self.vaccine_mapping)
        df = df[df.total_vaccinations > 0].replace(self.vaccine_mapping).dropna()
        df = df.groupby(["date", "vaccine"], as_index=False).sum()
        df = df.assign(location=self.location)
        df = df.pipe(self.make_monotonic, ["vaccine"])
        return df

    def pipe_get_totals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.fillna(0).sort_values("date")
        metrics = df.filter(like="change_").columns
        df[metrics] = df[metrics].cumsum()
        df.columns = df.columns.str.replace("change_", "total_")
        return df[df.total_vaccinations > 0]

    def pipe_rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns={"total_vaccinated": "people_fully_vaccinated"})

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        total_boosters = df.total_boosters_1 + df.total_boosters_2
        return df.assign(
            people_vaccinated=df.total_vaccinations - df.people_fully_vaccinated - total_boosters,
            total_boosters=total_boosters,
        )

    def pipe_vaccine_timeline(self, df: pd.DataFrame, df_man: pd.DataFrame) -> pd.DataFrame:
        vaccine_timeline = df_man[["date", "vaccine"]].groupby("vaccine").min().date.to_dict()
        vaccine_timeline["Pfizer/BioNTech"] = "2020-12-14"  # Vaccination start date
        return df.pipe(build_vaccine_timeline, vaccine_timeline)

    def pipe_filter_dp(self, df: pd.DataFrame) -> pd.DataFrame:
        df.loc[df.date.isin(["2022-07-29", "2022-07-30", "2022-07-31"]), "people_vaccinated"] = np.nan
        msk = df["date"] >= "2023-01-26"
        df.loc[msk, ["people_vaccinated", "people_fully_vaccinated"]] = np.nan
        return df

    def pipe_make_monotonic(self, df: pd.DataFrame) -> pd.DataFrame:
        num_filtered_dates = 0
        while True:
            try:
                df = df.pipe(self.make_monotonic, max_removed_rows=self.max_removed_rows)
            except Exception:
                if num_filtered_dates < self.max_filtered_dates:
                    # Filter the last dates if `make_monotonic()` fails
                    df = df.iloc[:-1]
                    num_filtered_dates += 1
                else:
                    raise
            else:
                break
        return df

    def pipeline(self, df: pd.DataFrame, df_man: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_get_totals)
            .pipe(self.pipe_rename_columns)
            .pipe(self.pipe_metrics)
            .pipe(self.pipe_vaccine_timeline, df_man)
            .pipe(self.pipe_filter_dp)
            .pipe(self.pipe_metadata)
            .pipe(self.pipe_make_monotonic)
            [
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

    def export(self):
        # Read
        df, df_age, df_man = self.read(), self.read_age(), self.read_manufacturer()
        # Transform
        df_age = df_age.pipe(self.pipeline_age)
        df_man = df_man.pipe(self.pipeline_manufacturer)
        df = df.pipe(self.pipeline, df_man)
        # Export
        self.export_datafile(
            df=df,
            df_age=df_age,
            df_manufacturer=df_man,
            meta_age={"source_name": self.source_name, "source_url": self.source_url_age},
            meta_manufacturer={"source_name": self.source_name, "source_url": self.source_url_man},
        )


def main():
    Canada().export()
