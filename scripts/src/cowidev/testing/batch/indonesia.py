import requests
import pandas as pd

from cowidev.testing import CountryTestBase


class Indonesia(CountryTestBase):
    location = "Indonesia"
    units = "people tested"
    source_url_ref = "https://covid19.go.id/peta-sebaran"
    source_label = "Government of Indonesia"

    def read(self):
        url = "https://data.covid19.go.id/public/api/pemeriksaan-vaksinasi.json"
        data = requests.get(url).json()
        df = pd.DataFrame(data["pemeriksaan"]["harian"])
        return df

    def pipeline(self, df: pd.DataFrame):
        df["Cumulative total"] = df.jumlah_orang_pcr_tcm_kum.apply(
            lambda x: x["value"]
        ) + df.jumlah_orang_antigen_kum.apply(lambda x: x["value"])

        df = (
            df[["key_as_string", "Cumulative total"]]
            .rename(columns={"key_as_string": "Date"})
            .sort_values("Date")
            .drop_duplicates(subset=["Cumulative total"], keep="first")
        )

        df = df.pipe(self.pipe_metadata)
        return df

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Indonesia().export()
