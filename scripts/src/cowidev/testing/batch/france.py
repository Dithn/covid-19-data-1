import pandas as pd

from cowidev.testing import CountryTestBase


class France(CountryTestBase):
    location = "France"
    units = "people tested"
    source_url_ref = (
        "https://www.data.gouv.fr/fr/datasets/donnees-relatives-aux-resultats-des-tests-virologiques-covid-19/"
    )
    source_label = "National Public Health Agency"

    def read(self):
        url = "https://www.data.gouv.fr/fr/datasets/r/d349accb-56ef-4b53-b218-46c2a7f902e0"
        df = pd.read_csv(url, sep=";", usecols=["jour", "cl_age90", "T", "P"])
        df["T"] = [int(x.replace(",00", "")) for x in df["T"]]
        df["P"] = [int(x.replace(",00", "")) for x in df["P"]]
        df = (
            df.rename(columns={"jour": "Date"})
            .groupby("Date", as_index=False)
            .agg(**{"Daily change in cumulative total": ("T", sum), "pos": ("P", sum)})
        )
        df["Positive rate"] = (
            (df["pos"].rolling(7).mean()) / (df["Daily change in cumulative total"].rolling(7).mean())
        ).round(3)
        return df

    def pipeline(self, df: pd.DataFrame):
        df = df.dropna(subset=["Daily change in cumulative total", "Positive rate"], how="all")
        df = df.pipe(self.pipe_metadata)
        return df

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    France().export()
