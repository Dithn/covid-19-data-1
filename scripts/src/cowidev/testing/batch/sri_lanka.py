import pandas as pd

from cowidev.utils.web import request_json
from cowidev.utils.clean import clean_date_series, clean_count
from cowidev.testing import CountryTestBase


class SriLanka(CountryTestBase):
    location: str = "Sri Lanka"
    units: str = "tests performed"
    source_label: str = "Sri Lanka Health Promotion Bureau"
    source_url: str = "https://www.hpb.health.gov.lk/api/get-current-statistical"
    source_url_ref: str = "https://www.hpb.health.gov.lk"
    rename_columns: dict = {
        "date": "Date",
    }

    def read(self) -> pd.DataFrame:
        """Reads data from source."""
        data = request_json(self.source_url)
        df = self._parse_data(data)
        return df

    def _parse_data(self, data: dict) -> pd.DataFrame:
        """Parses data from source."""
        pcr_df = pd.json_normalize(data, record_path=["data", "daily_pcr_testing_data"]).sort_values("date")
        art_df = pd.json_normalize(data, record_path=["data", "daily_antigen_testing_data"]).sort_values("date")
        df = pd.merge(pcr_df, art_df)
        return df

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans date column"""
        return df.assign(Date=clean_date_series(df["Date"], "%Y-%m-%d"))

    def pipe_metrics(self, df: pd.DataFrame):
        """Pipes metrics"""
        df = df.assign(
            **{
                "Daily change in cumulative total": (
                    df["antigen_count"].apply(clean_count) + df["pcr_count"].apply(clean_count)
                ),
            }
        )
        return df[df["Daily change in cumulative total"] > 0].drop_duplicates(subset="Date", keep="last")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """pipeline for data"""
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_date)
            .pipe(self.pipe_metrics)
            .pipe(self.pipe_metadata)
            .sort_values("Date")
        )

    def export(self):
        """Exports data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    SriLanka().export()
