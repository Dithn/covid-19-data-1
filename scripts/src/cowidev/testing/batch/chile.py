import pandas as pd

from cowidev.testing import CountryTestBase


class Chile(CountryTestBase):
    location = "Chile"
    source_url_ref = "https://github.com/MinCiencia/Datos-COVID19/tree/master/output/producto49"
    source_label = "Ministry of Health, via Ministry of Science GitHub repository"
    units = "tests performed"

    def export(self):
        pcr = pd.read_csv(
            "https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto49/Positividad_Diaria_Media_T.csv"
        )
        ag = pd.read_csv(
            "https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto49/Positividad_Diaria_Media_Ag_T.csv"
        )

        pcr = pcr[["Fecha", "pcr"]]
        ag = ag[["Fecha", "Ag"]]

        df = pd.merge(ag, pcr, on="Fecha", how="outer").fillna(0).sort_values("Fecha")
        df["Daily change in cumulative total"] = df["Ag"] + df["pcr"]
        df = df.rename(columns={"Fecha": "Date"})
        df = df.drop(["Ag", "pcr"], axis=1)

        df = df.pipe(self.pipe_metadata)

        self.export_datafile(df)


def main():
    Chile().export()
