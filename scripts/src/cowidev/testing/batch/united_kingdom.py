import pandas as pd
from uk_covid19 import Cov19API

from cowidev.testing import CountryTestBase
from cowidev.testing.utils import make_monotonic


class UnitedKingdom(CountryTestBase):
    location = "United Kingdom"
    source_url_ref = "https://coronavirus.data.gov.uk/details/testing"
    source_label = "Public Health England"
    units = "tests performed"

    def read(self) -> pd.DataFrame:
        filters = ["areaType=Overview"]
        structure = {
            "Date": "date",
            "cumPillarOne": "cumPillarOneTestsByPublishDate",
            "cumPillarTwo": "cumPillarTwoTestsByPublishDate",
        }
        api = Cov19API(filters=filters, structure=structure)
        df = api.get_dataframe()
        df["Cumulative total"] = df.cumPillarOne.fillna(method="ffill").fillna(0) + df.cumPillarTwo.fillna(
            method="ffill"
        ).fillna(0)
        # Filter invalid
        df = df.pipe(make_monotonic)
        return df

    def pipeline(self, df: pd.DataFrame):
        return df.pipe(self.pipe_metadata)

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    UnitedKingdom().export()
