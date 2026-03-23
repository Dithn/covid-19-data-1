import json
import requests
import pandas as pd
from cowidev.testing import CountryTestBase


class Portugal(CountryTestBase):
    location = "Portugal"
    source_url = "https://services5.arcgis.com/eoFbezv6KiXqcnKq/arcgis/rest/services/Covid19_Amostras/FeatureServer/0/query?f=json&where=1%3D1&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&orderByFields=Data_do_Relatorio%20asc&resultOffset=0&resultRecordCount=32000&resultType=standard&cacheHint=true"
    source_url_ref = "https://covid19.min-saude.pt/ponto-de-situacao-atual-em-portugal/"
    source_label = "Ministry of Health"
    units = "tests performed"

    def read(self):
        data = json.loads(requests.get(self.source_url).content)
        data = [elem["attributes"] for elem in data["features"]]

        df = pd.DataFrame.from_records(data)
        return df

    def pipeline(self, df: pd.DataFrame):
        df = df[["Total_Amostras__Ac", "Data_do_Relatorio"]].rename(
            columns={"Data_do_Relatorio": "Date", "Total_Amostras__Ac": "Cumulative total"}
        )
        df["Date"] = pd.to_datetime(df["Date"], unit="ms")
        df = df.pipe(self.pipe_metadata)
        return df

    def export(self):
        df = self.read().pipe(self.pipeline)

        self.export_datafile(df)


def main():
    Portugal().export()
