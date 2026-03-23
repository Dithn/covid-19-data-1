import pandas as pd

from cowidev.testing import CountryTestBase


class Czechia(CountryTestBase):
    location = "Czechia"
    source_url = "https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/testy-pcr-antigenni.csv"
    source_url_ref = "https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19"
    source_label = "Ministry of Health"
    units = "tests performed"
    rename_columns = {
        "datum": "Date",
        "pocet_PCR_testy": "pcr",
        "pocet_AG_testy": "antigen",
        "incidence_pozitivni": "positive",
    }

    def read(self):
        return pd.read_csv(
            self.source_url,
            usecols=["datum", "pocet_PCR_testy", "pocet_AG_testy", "incidence_pozitivni"],
        )

    def pipe_pr(self, df: pd.DataFrame) -> pd.DataFrame:
        pr = (df["positive"].rolling(7).sum() / df["Daily change in cumulative total"].rolling(7).sum()).round(3)
        df = df.assign(**{"Positive rate": pr})
        return df

    def pipe_metric(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(**{"Daily change in cumulative total": df.pcr + df.antigen})

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_rename_columns).pipe(self.pipe_metric).pipe(self.pipe_pr).pipe(self.pipe_metadata)

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Czechia().export()
