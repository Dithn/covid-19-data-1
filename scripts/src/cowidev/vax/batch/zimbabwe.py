import pandas as pd

from cowidev.utils.web import request_json
from cowidev.vax.utils.utils import build_vaccine_timeline
from cowidev.vax.utils.base import CountryVaxBase


class Zimbabwe(CountryVaxBase):
    source_url: str = "https://www.arcgis.com/home/webmap/viewer.html?url=https://services9.arcgis.com/DnERH4rcjw7NU6lv/ArcGIS/rest/services/Vaccine_Distribution_Program/FeatureServer&source=sd"
    location: str = "Zimbabwe"
    columns_rename: dict = {
        "date_reported": "date",
        "first_doses": "people_vaccinated",
        "second_doses": "people_fully_vaccinated",
        "third_doses": "total_boosters",
    }

    def read(self) -> pd.DataFrame:
        columns = "%2C".join(self.columns_rename.keys())
        url = f"https://services9.arcgis.com/DnERH4rcjw7NU6lv/arcgis/rest/services/Vaccine_Distribution_Program/FeatureServer/2/query?where=1%3D1&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&returnGeodetic=false&outFields={columns}&returnGeometry=true&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pjson&token="
        data = request_json(url)
        return pd.DataFrame.from_records(elem["attributes"] for elem in data["features"])

    def pipe_rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.columns_rename:
            return df.rename(columns=self.columns_rename)
        return df

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.fillna(0)
        df["total_vaccinations"] = df.people_vaccinated + df.people_fully_vaccinated + df.total_boosters
        df = df.groupby("date", as_index=False).sum().sort_values("date")
        df[["total_vaccinations", "people_vaccinated", "people_fully_vaccinated", "total_boosters"]] = (
            df[["total_vaccinations", "people_vaccinated", "people_fully_vaccinated", "total_boosters"]]
            .cumsum()
            .astype(int)
        )
        return df[df.total_vaccinations > 0]

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(date=pd.to_datetime(df.date, unit="ms").dt.date.astype(str))

    def pipe_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(
            location=self.location,
            source_url=self.source_url,
        )

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        df = build_vaccine_timeline(
            df,
            {
                "Sinopharm/Beijing": "2021-01-01",
                "Oxford/AstraZeneca": "2021-03-29",
                "Sinovac": "2021-03-30",
                "Sputnik V": "2021-06-11",
            },
        )
        return df

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_date)
            .pipe(self.pipe_metrics)
            .pipe(self.pipe_columns)
            .pipe(self.pipe_vaccine)
        )

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Zimbabwe().export()
