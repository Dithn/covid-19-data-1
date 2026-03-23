import pandas as pd

from cowidev.testing import CountryTestBase


class Lithuania(CountryTestBase):
    location = "Lithuania"
    units = "tests performed"
    source_label = "Government of Lithuania"
    source_url = "https://opendata.arcgis.com/datasets/d49a63c934be4f65a93b6273785a8449_0.csv?where=municipality_code%20%3D%20%2700%27"
    source_url_ref = "https://open-data-ls-osp-sdg.hub.arcgis.com/datasets/d49a63c934be4f65a93b6273785a8449_0"
    rename_columns = {
        "date": "Date",
        "dgn_pos_day": "daily_pos",
        "dgn_tot_day": "Daily change in cumulative total",
    }

    def read(self) -> pd.DataFrame:
        return pd.read_csv(self.source_url, usecols=["date", "dgn_pos_day", "dgn_tot_day"], parse_dates=["date"])

    def pipe_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df["Daily change in cumulative total"] > 0]

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.assign(Date=df.Date.dt.strftime("%Y-%m-%d"))
        return df.sort_values("Date")

    def pipe_pr(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(
            **{
                "Positive rate": (
                    df["daily_pos"].rolling(7).sum() / df["Daily change in cumulative total"].rolling(7).sum()
                ).round(3)
            }
        )

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_filter)
            .pipe(self.pipe_date)
            .pipe(self.pipe_pr)
            .pipe(self.pipe_metadata)
        )

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Lithuania().export()
