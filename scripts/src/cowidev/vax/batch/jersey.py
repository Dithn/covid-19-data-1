import requests
import tempfile
import re

import pandas as pd

from cowidev.vax.utils.base import CountryVaxBase


class Jersey(CountryVaxBase):
    def __init__(self):
        """Constructor.

        Args:
            source_url (str): Source data url
            location (str): Location name
            columns_rename (dict, optional): Maps original to new names. Defaults to None.
        """
        self.source_url = "https://www.gov.je/Datasets/ListOpenData?ListName=COVID19Weekly&clean=true"
        self.location = "Jersey"
        self.columns_rename = {
            "Date": "date",
            "VaccinationsTotalNumberDoses": "total_vaccinations",
            "VaccinationsTotalNumberFirstDoseVaccinations": "people_vaccinated",
            "VaccinationsTotalNumberSecondDoseVaccinations": "people_fully_vaccinated",
            "VaccinationsTotalNumberThirdDoseVaccinations": "total_boosters",
            "VaccinationsTotalNumberFourthDoseVaccinations": "total_boosters_2",
        }

    def read(self):
        with tempfile.NamedTemporaryFile() as tf:
            with open(tf.name, mode="wb") as f:
                f.write(requests.get(self.source_url).content)
            return pd.read_csv(tf.name)

    def pipe_select_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[self.columns_rename.keys()]

    def pipe_rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[self.columns_rename.keys()].rename(columns=self.columns_rename)

    def pipe_enrich_vaccine_name(self, df: pd.DataFrame) -> pd.DataFrame:
        def _enrich_vaccine(date: str) -> str:
            if date >= "2021-04-07":
                return "Moderna, Oxford/AstraZeneca, Pfizer/BioNTech"
            return "Oxford/AstraZeneca, Pfizer/BioNTech"

        return df.assign(vaccine=df.date.astype(str).apply(_enrich_vaccine))

    def pipe_enrich_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(location=self.location, source_url=self.source_url)

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(total_boosters=df.total_boosters + df.total_boosters_2.fillna(0))

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_select_columns)
            .pipe(self.pipe_rename_columns)
            .pipe(self.pipe_enrich_vaccine_name)
            .pipe(self.pipe_enrich_columns)
            .pipe(self.pipe_metrics)
            .pipe(self.pipe_filter_dp, ["2022-10-02"], ["total_boosters"])
            .sort_values("date")[
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

    def pipe_age_select_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        # print(df.columns[-15:])
        return df[
            [
                "Date",
                "VaccinationsPercentagePopulationVaccinatedFirstDose80yearsandover",
                "VaccinationsPercentagePopulationVaccinatedFirstDose75to79years",
                "VaccinationsPercentagePopulationVaccinatedFirstDose70to74years",
                "VaccinationsPercentagePopulationVaccinatedFirstDose65to69years",
                "VaccinationsPercentagePopulationVaccinatedFirstDose60to64years",
                "VaccinationsPercentagePopulationVaccinatedFirstDose55to59years",
                "VaccinationsPercentagePopulationVaccinatedFirstDose50to54years",
                "VaccinationsPercentagePopulationVaccinatedFirstDose40to49years",
                "VaccinationsPercentagePopulationVaccinatedFirstDose30to39years",
                "VaccinationsPercentagePopulationVaccinatedFirstDose18to29years",
                "VaccinationsPercentagePopulationVaccinatedFirstDose16to17years",
                "VaccinationsPercentagePopulationVaccinatedFirstDose12to15years",
                "VaccinationsPercentagePopulationVaccinatedFirstDose5to11years",
                # "VaccinationsPercentagePopulationVaccinatedFirstDose0to5years",
                "VaccinationsPercentagePopulationVaccinatedSecondDose80yearsandover",
                "VaccinationsPercentagePopulationVaccinatedSecondDose75to79years",
                "VaccinationsPercentagePopulationVaccinatedSecondDose70to74years",
                "VaccinationsPercentagePopulationVaccinatedSecondDose65to69years",
                "VaccinationsPercentagePopulationVaccinatedSecondDose60to64years",
                "VaccinationsPercentagePopulationVaccinatedSecondDose55to59years",
                "VaccinationsPercentagePopulationVaccinatedSecondDose50to54years",
                "VaccinationsPercentagePopulationVaccinatedSecondDose40to49years",
                "VaccinationsPercentagePopulationVaccinatedSecondDose30to39years",
                "VaccinationsPercentagePopulationVaccinatedSecondDose18to29years",
                "VaccinationsPercentagePopulationVaccinatedSecondDose16to17years",
                "VaccinationsPercentagePopulationVaccinatedSecondDose12to15years",
                "VaccinationsPercentagePopulationVaccinatedSecondDose5to11years",
                # "VaccinationsPercentagePopulationVaccinatedSecondDose0to5years",
                "VaccinationsPercentagePopulationVaccinatedThirdDose80yearsandover",
                "VaccinationsPercentagePopulationVaccinatedThirdDose75to79years",
                "VaccinationsPercentagePopulationVaccinatedThirdDose70to74years",
                "VaccinationsPercentagePopulationVaccinatedThirdDose65to69years",
                "VaccinationsPercentagePopulationVaccinatedThirdDose60to64years",
                "VaccinationsPercentagePopulationVaccinatedThirdDose55to59years",
                "VaccinationsPercentagePopulationVaccinatedThirdDose50to54years",
                "VaccinationsPercentagePopulationVaccinatedThirdDose40to49years",
                "VaccinationsPercentagePopulationVaccinatedThirdDose30to39years",
                "VaccinationsPercentagePopulationVaccinatedThirdDose18to29years",
                "VaccinationsPercentagePopulationVaccinatedThirdDose16to17years",
                "VaccinationsPercentagePopulationVaccinatedThirdDose12to15years",
                "VaccinationsPercentagePopulationVaccinatedThirdDose5to11years",
                # "VaccinationsPercentagePopulationVaccinatedThirdDose0to5years",
                "VaccinationsPercentagePopulationVaccinatedFourthDose80yearsandover",
                "VaccinationsPercentagePopulationVaccinatedFourthDose75to79years",
                "VaccinationsPercentagePopulationVaccinatedFourthDose70to74years",
                "VaccinationsPercentagePopulationVaccinatedFourthDose65to69years",
                "VaccinationsPercentagePopulationVaccinatedFourthDose60to64years",
                "VaccinationsPercentagePopulationVaccinatedFourthDose55to59years",
                "VaccinationsPercentagePopulationVaccinatedFourthDose50to54years",
                "VaccinationsPercentagePopulationVaccinatedFourthDose40to49years",
                "VaccinationsPercentagePopulationVaccinatedFourthDose30to39years",
                "VaccinationsPercentagePopulationVaccinatedFourthDose18to29years",
                "VaccinationsPercentagePopulationVaccinatedFourthDose16to17years",
                "VaccinationsPercentagePopulationVaccinatedFourthDose12to15years",
                "VaccinationsPercentagePopulationVaccinatedFourthDose5to11years",
            ]
        ]

    def _extract_age_group(self, age_group_raw):
        # regex_17 = r"VaccinationsPercentagePopulationVaccinated(?:First|Second|Third)Dose17yearsandunder"
        regex_80 = r"VaccinationsPercentagePopulationVaccinated(?:First|Second|Third|Fourth)Dose80yearsandover"
        regex = r"VaccinationsPercentagePopulationVaccinated(?:First|Second|Third|Fourth)Dose(\d+)to(\d+)years"
        # if re.match(regex_17, age_group_raw):
        #     age_group = "0-17"
        if re.match(regex_80, age_group_raw):
            age_group = "80-"
        elif re.match(regex, age_group_raw):
            age_group = "-".join(re.match(regex, age_group_raw).group(1, 2))
        return age_group

    def pipe_age_create_groups(self, df: pd.DataFrame) -> pd.DataFrame:
        # Split data in dataframes with first and second doses
        df1 = df.filter(regex=r"Date|VaccinationsPercentagePopulationVaccinatedFirstDose.*")
        df2 = df.filter(regex=r"Date|VaccinationsPercentagePopulationVaccinatedSecondDose.*")
        df3 = df.filter(regex=r"Date|VaccinationsPercentagePopulationVaccinatedThirdDose.*")
        df4 = df.filter(regex=r"Date|VaccinationsPercentagePopulationVaccinatedFourthDose.*")
        # Melt dataframes
        df1 = df1.melt(
            id_vars="Date",
            var_name="age_group",
            value_name="people_vaccinated_per_hundred",
        )
        df2 = df2.melt(
            id_vars="Date",
            var_name="age_group",
            value_name="people_fully_vaccinated_per_hundred",
        )
        df3 = df3.melt(
            id_vars="Date",
            var_name="age_group",
            value_name="people_with_booster_per_hundred",
        )
        df4 = df4.melt(
            id_vars="Date",
            var_name="age_group",
            value_name="people_with_booster_2_per_hundred",
        )
        # Process and merge dataframes
        df1 = df1.assign(age_group=df1.age_group.apply(self._extract_age_group))
        df2 = df2.assign(age_group=df2.age_group.apply(self._extract_age_group))
        df3 = df3.assign(age_group=df3.age_group.apply(self._extract_age_group))
        df4 = df4.assign(age_group=df4.age_group.apply(self._extract_age_group))
        df = df1.merge(df2, on=["Date", "age_group"]).dropna(subset=["Date"])
        df = df.merge(df3, on=["Date", "age_group"]).dropna(subset=["Date"])
        return df

    def pipe_age_rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns={"Date": "date"})

    def pipe_age_minmax_values(self, df: pd.DataFrame) -> pd.DataFrame:
        df[["age_group_min", "age_group_max"]] = df.age_group.str.split("-", expand=True)
        return df

    def pipe_metrics_scale_100(self, df: pd.DataFrame) -> pd.DataFrame:
        column_metrics = [
            "people_vaccinated_per_hundred",
            "people_fully_vaccinated_per_hundred",
            "people_with_booster_per_hundred",
        ]
        df[column_metrics] = (df[column_metrics] * 100).round(2)
        return df

    def pipe_age_fix_dp(self, df: pd.DataFrame) -> pd.DataFrame:
        column_metrics = [
            "people_vaccinated_per_hundred",
            "people_fully_vaccinated_per_hundred",
            "people_with_booster_per_hundred",
        ]
        dt_min = "2021-09-05"
        dt_max = "2021-09-22"
        msk = (df.date >= dt_min) & (df.date <= dt_max)
        df.loc[msk, column_metrics] = df.loc[msk, column_metrics] * 100
        msk = df[column_metrics] > 100
        if (df[column_metrics] > 100).any(None):
            raise ValueError(f"Check fixed datapoints ({dt_min}<date<{dt_max}), they might be already fine!")
        return df

    def pipe_age_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        df.loc[(df.date == "2021-08-29"), "people_fully_vaccinated_per_hundred"] = None
        df.loc[(df.date == "2021-09-05") & (df.age_group_min == "18"), "people_vaccinated_per_hundred"] = None
        df.loc[(df.date == "2021-09-05") & (df.age_group_min == "40"), "people_vaccinated_per_hundred"] = None
        return df
        # df.pipe(make_monotonic, "date", ["people_vaccinated_per_hundred", "people_fully_vaccinated_per_hundred"])

    def pipeline_age(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_age_select_columns)
            .pipe(self.pipe_age_create_groups)
            .pipe(self.pipe_age_rename_columns)
            # .pipe(
            #     self.pipe_filter_dp,
            #     ["2022-09-18", "2022-10-02", "2022-10-09", "2022-10-16"],
            # )
            # .pipe(self.make_monotonic, ["age_group"])
            .pipe(self.pipe_age_minmax_values)
            .pipe(self.pipe_enrich_columns)
            .pipe(self.pipe_metrics_scale_100)
            # .pipe(self.pipe_age_fix_dp)
            .pipe(self.pipe_age_filter)
            .sort_values(["date", "age_group_min"])[
                [
                    "location",
                    "date",
                    "age_group_min",
                    "age_group_max",
                    "people_vaccinated_per_hundred",
                    "people_fully_vaccinated_per_hundred",
                    "people_with_booster_per_hundred",
                ]
            ]
        )

    def pipeline_base(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.drop_duplicates()
            .sort_values(["Date", "VaccinationsPercentagePopulationVaccinatedFirstDose80yearsandover"])
            .drop_duplicates("Date", keep="last")
        )

    def export(self):
        """Generalized."""
        df_base = self.read().pipe(self.pipeline_base)
        # Main data
        df = df_base.pipe(self.pipeline)
        # Age data
        df_age = df_base.pipe(self.pipeline_age)
        # Export
        self.export_datafile(
            df, df_age=df_age, meta_age={"source_name": "Government of Jersey", "source_url": self.source_url}
        )


def main():
    Jersey().export()
