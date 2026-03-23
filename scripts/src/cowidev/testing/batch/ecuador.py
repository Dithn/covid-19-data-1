import pandas as pd

from cowidev.utils.clean import clean_date
from cowidev.testing.utils import make_monotonic
from cowidev.testing.utils.base import CountryTestBase


class Ecuador(CountryTestBase):
    location: str = "Ecuador"
    units: str = "people tested"
    notes: str = "Sum of confirmados and descartados"
    source_url_ref: str = "https://github.com/andrab/ecuacovid"
    source_url: str = "https://github.com/andrab/ecuacovid/raw/master/datos_crudos/ecuacovid.csv"
    source_label: str = f"Ministerio de Salud Pública del Ecuador (via Ecuacovid)"
    rename_columns: dict = {
        "created_at": "Date",
        "positivas_pcr": "positive",
        "negativas_pcr": "negative",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        df = pd.read_csv(self.source_url, usecols=["created_at", "positivas_pcr", "negativas_pcr"])
        return df

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate metrics"""
        return df.assign(**{"Cumulative total": df[["positive", "negative"]].sum(axis=1)})

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert date to datetime"""
        return df.assign(Date=df.Date.apply(clean_date, fmt="%d/%m/%Y", minus_days=1))

    def pipe_pr(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate positive rate"""
        df = df.sort_values("Date")
        cases_over_period = df["positive"].diff().rolling(7).sum()
        tests_over_period = df["Cumulative total"].diff().rolling(7).sum()
        df = df.assign(**{"Positive rate": (cases_over_period / tests_over_period).round(3)}).fillna(0)
        df = df[df["Positive rate"] >= 0]
        return df.drop_duplicates(subset="Cumulative total")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data"""
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_metrics)
            .pipe(self.pipe_date)
            .pipe(self.pipe_pr)
            .pipe(self.pipe_metadata)
            .pipe(make_monotonic)
        )

    def export(self):
        """Export data to CSV"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, float_format="%.3f")


def main():
    Ecuador().export()
