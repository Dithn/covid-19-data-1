from cowidev.vax.utils.base import CountryVaxBase
import pandas as pd

from cowidev.utils.clean import clean_date_series
from cowidev.utils.web import request_json
from cowidev.vax.utils.files import load_query, load_data
from cowidev.vax.utils.utils import build_vaccine_timeline, make_monotonic


class TrinidadTobago(CountryVaxBase):
    source_ref = "https://experience.arcgis.com/experience/59226cacd2b441c7a939dca13f832112/"
    source = (
        "https://services3.arcgis.com/x3I4DqUw3b3MfTwQ/arcgis/rest/services/service_7a519502598f492a9094fd0ad503cf80/"
        "FeatureServer/0/query"
    )
    location: str = "Trinidad and Tobago"

    def read(self) -> pd.DataFrame:
        params = load_query("trinidad-and-tobago-metrics", to_str=False)
        data = request_json(self.source, params=params)
        return self._parse_data(data)

    def _parse_data(self, data: dict) -> int:
        records = [
            {
                "date": x["attributes"]["report_date_str"],
                # ppl vaxxed with 2-dose vax fd
                "people_vaccinated_2dosevax": x["attributes"]["total_vaccinated"],
                # ppl vaxxed with second dose of a 2-dose vax
                "people_fully_vaccinated_2dosevax": x["attributes"]["sd_total_second_dose"],
                # ppl fully vaxxed (second dose of a 2-dose vax or single shot)
                "people_fully_vaccinated": x["attributes"]["total_second_dose"],
                # doses of specific brands
                "d1_jj": x["attributes"]["fd_j_and_j"],
                "d1_pfizer": x["attributes"]["fd_pfizer"],
                "d1_sinopharm": x["attributes"]["fd_sinopharm"],
                # "d1_astrazeneca": x["attributes"]["fd_astrazeneca"],
                # booster doses
                "total_boosters": x["attributes"]["additional_primary_dose"],
            }
            for x in data["features"]
        ]
        return pd.DataFrame.from_records(records)

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(date=clean_date_series(df.date, "%d/%m/%Y")).sort_values("date")

    def pipe_vaccine_name(self, df: pd.DataFrame) -> pd.DataFrame:
        vaccine_timeline = {
            "Oxford/AstraZeneca": "2021-02-15",
            "Johnson&Johnson": df.loc[df.d1_jj.notnull(), "date"].min(),
            "Pfizer/BioNTech": df.loc[df.d1_pfizer.notnull(), "date"].min(),
            "Sinopharm/Beijing": df.loc[df.d1_sinopharm.notnull(), "date"].min(),
        }
        return (
            df.pipe(build_vaccine_timeline, vaccine_timeline)
            .drop(columns=["d1_pfizer", "d1_sinopharm"])
            .dropna(subset=["people_vaccinated_2dosevax"])
        )

    def pipe_checks(self, df: pd.DataFrame) -> pd.DataFrame:
        df_ = df.dropna(subset=["people_fully_vaccinated_2dosevax", "d1_jj", "people_fully_vaccinated"], how="any")
        diff = (
            df_["people_fully_vaccinated_2dosevax"].fillna(method="ffill")
            + df_["d1_jj"].fillna(method="ffill")
            - df_["people_fully_vaccinated"]
        ).apply(abs) / df_["people_fully_vaccinated"]
        msk = diff > 0.01
        if msk.any():
            raise ValueError(f"Fully vasccinated != single_dose + second_dose ({len(df_[msk])}):\n {df_[msk]}")
        return df

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df["people_fully_vaccinated"] = df.people_fully_vaccinated.fillna(method="ffill")
        df["people_vaccinated"] = df.people_vaccinated_2dosevax.fillna(method="ffill").fillna(0) + df.d1_jj.fillna(
            method="ffill"
        ).fillna(0)
        df["total_vaccinations"] = (
            df.people_vaccinated.fillna(method="ffill").fillna(0)
            + df.people_fully_vaccinated_2dosevax.fillna(method="ffill").fillna(0)
            + df.total_boosters.fillna(method="ffill").fillna(0)
        )
        return df

    def pipe_location(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(location=self.location)

    def pipe_source(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(source_url=self.source)

    def pipe_legacy(self, df: pd.DataFrame) -> pd.DataFrame:
        df_legacy = load_data("trinidad-and-tobago-legacy")
        df_legacy = df_legacy[~df_legacy.date.isin(df.date)]
        return pd.concat([df, df_legacy]).sort_values("date")

    def pipe_filter_dp(self, df: pd.DataFrame) -> pd.DataFrame:
        dates_exclude = ["2022-01-10"]
        return df[~df.date.isin(dates_exclude)]

    def pipe_out_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[
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

    def pipe_data_correction(self, df: pd.DataFrame) -> pd.DataFrame:
        # Row with typo in number of boosters
        return df[-df.date.isin(["2022-02-07", "2022-04-18"])]

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_date)
            .pipe(self.pipe_vaccine_name)
            .pipe(self.pipe_checks)
            .pipe(self.pipe_metrics)
            .pipe(self.pipe_location)
            .pipe(self.pipe_source)
            .pipe(self.pipe_legacy)
            .pipe(self.pipe_filter_dp)
            .pipe(self.pipe_out_columns)
            .pipe(self.pipe_data_correction)
            .pipe(self.make_monotonic, max_removed_rows=30)
        )

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    TrinidadTobago().export()
