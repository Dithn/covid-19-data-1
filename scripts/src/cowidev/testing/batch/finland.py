import pandas as pd

from cowidev.testing import CountryTestBase


class Finland(CountryTestBase):
    location = "Finland"
    units = "tests performed"
    base_url = "https://sampo.thl.fi/pivot/prod/en/epirapo/covid19case/fact_epirapo_covid19case.csv"
    source_url = f"{base_url}?row=dateweek20200101-509093L&column=measure-444833.445356.492118.&&fo=1"
    source_url_ref = "https://sampo.thl.fi/pivot/prod/en/epirapo/covid19case/fact_epirapo_covid19case"
    source_label = "Finnish Department of Health and Welfare"

    def read(self) -> pd.DataFrame:
        return pd.read_csv(self.source_url, delimiter=";")

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df["Time"] = pd.to_datetime(df["Time"], format="%Y-%m-%d")
        df = df.pivot(index="Time", columns="Measure", values="val").fillna(0).reset_index()
        df = (
            df.rename(
                columns={
                    "Time": "Date",
                    "Number of cases": "positive",
                    "Number of tests": "Daily change in cumulative total",
                }
            )
            .drop(columns=["Number of deaths"])
            .sort_values("Date")
        )

        df["Daily change in cumulative total"] = pd.to_numeric(
            df["Daily change in cumulative total"], downcast="integer"
        )
        df = df[df["Daily change in cumulative total"] != 0]

        df["Positive rate"] = (
            df["positive"].rolling(7).sum() / df["Daily change in cumulative total"].rolling(7).sum()
        ).round(3)

        return df

    def pipe_filter_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[["Date", "Daily change in cumulative total", "Positive rate"]].head(-1)

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_metrics).pipe(self.pipe_filter_columns).pipe(self.pipe_metadata)

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Finland().export()
