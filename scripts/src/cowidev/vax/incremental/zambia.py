from datetime import datetime

import pandas as pd

from cowidev.utils.clean import clean_date
from cowidev.utils.web import request_json
from cowidev.vax.utils.incremental import enrich_data, increment
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.utils import add_latest_who_values


class Zambia(CountryVaxBase):
    def __init__(self) -> None:
        self.location = "Zambia"
        self.source_url = (
            "https://services7.arcgis.com/OwPYxdqWv7612O7N/arcgis/rest/services/"
            "service_ef4ce56ba48a44ef82991dcf85f62f71/FeatureServer/0/query?f=json&&cacheHint=true&resultOffset=0&"
            "resultRecordCount=100&where=1=1&outFields=*&resultType=standard&returnGeometry=false&"
            "spatialRel=esriSpatialRelIntersects"
        )
        self.source_url_ref = "https://rtc-planning.maps.arcgis.com/apps/dashboards/3b3a01c1d8444932ba075fb44b119b63"

    def read(self):
        data = request_json(self.source_url)["features"][0]["attributes"]
        date = clean_date(datetime.fromtimestamp(data["EditDate"] / 1000))

        return pd.Series(
            {
                "total_vaccinations": data["Vaccine_total"],
                "people_fully_vaccinated": data["Vaccine_total_last24"],
                "date": date,
            }
        )

    def pipe_location(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "location", self.location)

    def pipe_source(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "source_url", self.source_url_ref)

    def pipe_vaccine(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "vaccine", "Johnson&Johnson, Oxford/AstraZeneca, Sinopharm/Beijing")

    def pipe_to_df(self, ds: pd.Series) -> pd.DataFrame:
        return pd.DataFrame(ds).T

    def pipe_filter_dp(self, df: pd.DataFrame) -> pd.Series:
        """There were duplicates on the 2022-12-01. This was a temporary fix."""
        date = "2022-12-01"
        msk = df["date"] == date
        if df.loc[msk, "total_vaccinations"].item() > 80e6:
            df.loc[msk, "total_vaccinations"] = None
        if df.loc[msk, "people_fully_vaccinated"].item() > 80e6:
            df.loc[msk, "people_fully_vaccinated"] = None
        df = df.dropna(subset=["total_vaccinations", "people_fully_vaccinated", "people_vaccinated"], how="all")
        return df

    def pipeline(self, ds: pd.Series) -> pd.Series:
        return (
            ds.pipe(self.pipe_location)
            .pipe(self.pipe_source)
            .pipe(self.pipe_vaccine)
            .pipe(self.pipe_to_df)
            .pipe(add_latest_who_values, "Zambia", ["people_vaccinated"])
            # .pipe(self.pipe_filter_dp)
        )

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df=df, attach=True)


def main():
    Zambia().export()
