import pandas as pd
import datetime

from cowidev.testing import CountryTestBase


class Spain(CountryTestBase):
    date = (datetime.date.today()).strftime("%d%m%Y")
    base_url = "https://www.sanidad.gob.es/profesionales/saludPublica/ccayes/alertasActual/nCov"
    test_url = f"{base_url}/documentos/Datos_Pruebas_Realizadas_Historico_{date}.csv"

    location = "Spain"
    units = "tests performed"
    source_label = "Ministry of Health"
    source_url = test_url
    source_url_ref = f"{base_url}/pruebasRealizadas.htm"

    def read(self) -> pd.DataFrame:
        df = pd.read_csv(self.test_url, encoding="cp1252", delimiter=";")
        df = df.drop(["PROVINCIA"], axis=1)
        df = df.rename(columns={"FECHA_PRUEBA": "Date"})
        df["Date"] = pd.to_datetime(df["Date"], format="%d%b%Y")
        df = df.groupby(["Date"])[["N_ANT_POSITIVOS", "N_PCR_POSITIVOS", "N_ANT", "N_PCR"]].apply(sum).reset_index()
        return df

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df["positive"] = df["N_ANT_POSITIVOS"] + df["N_PCR_POSITIVOS"]
        df["Daily change in cumulative total"] = df["N_ANT"] + df["N_PCR"]
        df["Daily change in cumulative total"] = pd.to_numeric(
            df["Daily change in cumulative total"], downcast="integer"
        )
        df = df[df["Daily change in cumulative total"] != 0]
        df["Positive rate"] = (
            df["positive"].rolling(7).sum() / df["Daily change in cumulative total"].rolling(7).sum()
        ).round(3)
        df["Positive rate"] = df["Positive rate"].fillna(0)
        return df

    def pipe_filter_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[["Date", "Daily change in cumulative total", "Positive rate"]]

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_metrics).pipe(self.pipe_filter_columns).pipe(self.pipe_metadata)

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Spain().export()
