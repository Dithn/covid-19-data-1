import pandas as pd
import numpy as np

from cowidev.utils import clean_date_series
from cowidev.utils.web import request_json
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.files import load_query
from cowidev.vax.utils.utils import build_vaccine_timeline


class Ireland(CountryVaxBase):
    location = "Ireland"
    source_url_ref = "https://covid19ireland-geohive.hub.arcgis.com/"
    source_url = {
        "primary": "https://services-eu1.arcgis.com/z6bHNio59iTqqSUY/ArcGIS/rest/services/COVID19_Daily_Vaccination/FeatureServer/0/query?where=1%3D1&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&relationParam=&returnGeodetic=false&outFields=*&returnGeometry=true&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&defaultSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&orderByFields=VaccinationDate+desc&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pjson&token=",
        "booster": "https://services-eu1.arcgis.com/z6bHNio59iTqqSUY/arcgis/rest/services/COVID19_HSE_vaccine_booster_dose_daily/FeatureServer/0/query",
    }

    def read(self) -> pd.DataFrame:
        params = load_query("ireland-metrics", to_str=False)

        data_primary = request_json(self.source_url["primary"])
        data_primary = self._parse_data_primary(data_primary)

        data_booster = request_json(self.source_url["booster"], params=params)
        data_booster = self._parse_data_boosters(data_booster)

        df = pd.merge(data_primary, data_booster, how="outer", on="date", validate="one_to_one")

        df = df.sort_values("date").ffill()

        return df
    def _parse_data_primary(self, data: dict) -> int:
        records = [
            {
                "date": x["attributes"]["VaccinationDate"],
                "dose_1": x["attributes"]["Dose1Cum"],
                "dose_2": x["attributes"]["Dose2Cum"],
                "single_dose": x["attributes"]["SingleDoseCum"],
                "people_vaccinated": x["attributes"]["PartiallyVacc"],
                "people_fully_vaccinated": x["attributes"]["FullyVacc"],
            }
            for x in data["features"]
        ]
        df = pd.DataFrame.from_records(records)
        # Sort
        df = df.sort_values("date")
        df = df.pipe(self.pipe_date)
        return df

    def _parse_data_boosters(self, data: dict) -> int:
        records = [
            {
                "date": x["attributes"]["VaccinationDate"],
                "immuno_doses": x["attributes"]["ImmunoDoseCum"],
                "immuno_doses2": x["attributes"]["ImmunoDoseCum2"],
                "immuno_doses3": x["attributes"]["ImmunoDoseCum3"],
                "immuno_doses4": x["attributes"]["ImmunoDoseCum4"],
                "additional_doses": x["attributes"]["AdditionalDoseCum"],
                "additional_doses_2": x["attributes"]["AdditionalDoseCum2"],
                "additional_doses_3": x["attributes"]["AdditionalDoseCum3"],
                "additional_doses_4": x["attributes"]["AdditionalDoseCum4"],
            }
            for x in data["features"]
        ]
        df = pd.DataFrame.from_records(records)
        # Sort
        df = df.sort_values("date")
        df = df.pipe(self.pipe_date)
        return df

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(
            total_vaccinations=df.dose_1 + df.dose_2 + df.single_dose + df.immuno_doses + df.additional_doses,
            total_boosters=df.immuno_doses + df.additional_doses,
        ).drop(columns=["dose_1", "dose_2", "single_dose", "immuno_doses", "additional_doses"])

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.assign(date=clean_date_series(df.date, unit="ms"))
            .sort_values("date")
            .drop_duplicates(subset=["date"], keep=False)
        )

    def pipe_vaccine(self, df: pd.DataFrame) -> str:
        return build_vaccine_timeline(
            df,
            {
                "Pfizer/BioNTech": "2020-12-01",
                "Moderna": "2021-02-05",
                "Oxford/AstraZeneca": "2021-02-05",
                "Johnson&Johnson": "2021-05-06",
                # Source: https://www.ecdc.europa.eu/en/publications-data/data-covid-19-vaccination-eu-eea
                "Novavax": "2022-02-04",
            },
        )

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(source_url=self.source_url_ref, location=self.location)

    def pipe_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        msk = df.date.isin(
            [
                "2022-03-17",
                "2022-04-16",
                "2022-10-31",
                "2022-12-24",
                "2022-12-26",
                "2022-12-27",
                "2023-01-01",
                "2023-01-02",
                "2023-03-17",
                "2023-03-26",
                "2023-04-08",
                "2023-04-09",
                "2023-04-23",
                "2023-04-24",
                "2023-04-26",
                "2023-04-30",
                "2023-06-24",
                "2023-07-01",
                "2023-07-02",
                "2023-07-07",
                "2023-07-14",
                "2023-07-16",
                "2023-07-20",
                "2023-07-22",
                "2023-07-29",
                "2023-08-04",
                "2023-08-05",
                "2023-08-06",
                "2023-08-07",
                "2023-08-11",
                "2023-08-12",
                "2023-08-19",
                "2023-08-20",
                "2023-08-26",
                "2023-08-29",
                "2023-09-10",
                "2023-09-12",
                "2023-09-23",
                "2023-09-24",
                "2023-10-14"
            ]
        )

        # for col in ["total_vaccinations", "people_vaccinated", "people_fully_vaccinated", "total_boosters"]:
        if (df.loc[msk, ["people_vaccinated", "people_fully_vaccinated"]] == 0).any(axis=None):
            df = df.loc[~msk]
        # dt_limit = "2023-10-25"
        # df.loc[df["date"] >= dt_limit, ["people_vaccinated", "people_fully_vaccinated"]] = np.nan
        
        # Boosters
        df.loc[df["date"].isin(["2023-09-09", "2022-12-25"]), "total_boosters"] = np.nan

        # Just drop rows
        df = df[~df["date"].isin([
            "2022-12-25",
            "2023-09-16",
            "2023-12-31",
            "2024-01-01",

        ])]
        return df

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.fillna(0)
            .pipe(self.pipe_metrics)
            # .pipe(self.pipe_date)
            .pipe(self.pipe_metadata)
            .pipe(self.pipe_vaccine)
            .pipe(self.pipe_filter)
            .sort_values("date")[
                [
                    "location",
                    "date",
                    "total_vaccinations",
                    "people_vaccinated",
                    "people_fully_vaccinated",
                    "total_boosters",
                    "vaccine",
                    "source_url",
                ]
            ]
        )

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Ireland().export()
