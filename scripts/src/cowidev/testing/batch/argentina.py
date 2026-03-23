import pandas as pd

from cowidev.testing import CountryTestBase


class Argentina(CountryTestBase):
    location: str = "Argentina"
    units: str = "tests performed"
    source_label: str = "Government of Argentina"
    source_url: str = "https://sisa.msal.gov.ar/datos/descargas/covid-19/files/Covid19Determinaciones.zip"
    source_url_ref: str = "https://datos.gob.ar/dataset/salud-covid-19-determinaciones-registradas-republica-argentina"
    rename_columns: dict = {"fecha": "Date", "total": "Daily change in cumulative total", "positivos": "positive"}

    def read(self) -> pd.DataFrame:
        df = pd.read_csv(
            "https://sisa.msal.gov.ar/datos/descargas/covid-19/files/Covid19Determinaciones.zip",
            usecols=["fecha", "total", "positivos"],
        )
        return df

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        # Occasional errors where some lab inserts data before 2020
        df = df[df.Date >= "2020"]
        # Groupby
        df = df.groupby("Date", as_index=False).sum()
        # PR
        df["Positive rate"] = (
            df.positive.rolling(7).sum().div(df["Daily change in cumulative total"].rolling(7).sum()).round(3)
        )
        # Clean
        df = df[df["Daily change in cumulative total"] > 0].drop(columns=["positive"])
        return df

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_rename_columns).pipe(self.pipe_metrics).pipe(self.pipe_metadata)

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Argentina().export()
