import pandas as pd

from cowidev.utils.utils import check_known_columns
from cowidev.utils.web import request_json
from cowidev.vax.utils.utils import add_latest_who_values
from cowidev.vax.utils.base import CountryVaxBase


class SaudiArabia(CountryVaxBase):
    location = "Saudi Arabia"
    source_url = "https://services6.arcgis.com/bKYAIlQgwHslVRaK/arcgis/rest/services/Vaccination_Individual_Total/FeatureServer/0/query?f=json&cacheHint=true&outFields=*&resultType=standard&returnGeometry=false&spatialRel=esriSpatialRelIntersects&where=1%3D1"
    source_url_ref = "https://covid19.moh.gov.sa/"

    def read(self):
        data = request_json(self.source_url)
        df = pd.DataFrame.from_records(elem["attributes"] for elem in data["features"])
        check_known_columns(
            df,
            [
                "Reportdt",
                "Total_Vaccinations",
                "Total_Individuals",
                "LastValue",
                "ObjectId",
                "Elderly",
                "FirstDose",
                "SecondDose",
                "BoosterDose",
            ],
        )
        return df

    def pipeline(self, df: pd.DataFrame):
        df = df.drop(columns=["ObjectId", "LastValue", "Total_Individuals"])

        df = df.rename(
            columns={
                "Reportdt": "date",
                "Total_Vaccinations": "total_vaccinations",
                "FirstDose": "people_vaccinated",
                "SecondDose": "people_fully_vaccinated",
                "BoosterDose": "total_boosters",
            }
        )

        df["date"] = pd.to_datetime(df.date, unit="ms").dt.date.astype(str)

        df = df.groupby("date", as_index=False).max()

        df = df.assign(
            location=self.location,
            source_url=self.source_url_ref,
            vaccine="Pfizer/BioNTech",
        )
        df.loc[df.date >= "2021-02-18", "vaccine"] = "Oxford/AstraZeneca, Pfizer/BioNTech"

        df = df[df.total_vaccinations > 0].sort_values("date")

        return df.pipe(self.make_monotonic).pipe(
            add_latest_who_values,
            who_location_name="Saudi Arabia",
            metrics=["total_vaccinations", "people_vaccinated", "people_fully_vaccinated"],
        )[
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

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    SaudiArabia().export()
