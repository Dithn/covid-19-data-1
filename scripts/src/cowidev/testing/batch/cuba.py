import requests

import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.utils import clean_date


class Cuba(CountryTestBase):
    source_url = (
        "https://raw.githubusercontent.com/covid19cubadata/covid19cubadata.github.io/master/data/covid19-cuba.json"
    )
    source_url_ref = "https://covid19cubadata.github.io/#cuba"
    location = "Cuba"
    units = "tests performed"
    notes = "Made available on GitHub by covid19cubadata"
    source_label = "Ministry of Public Health"

    def read(self):
        data = requests.get(self.source_url).json()
        data = data["casos"]["dias"]
        data = list(data.values())
        df = self._parse_data(data)
        return df

    def _parse_data(self, data):
        records = []
        for elem in data:
            if "tests_total" in elem:
                records.append(
                    {
                        "Date": clean_date(elem["fecha"], "%Y/%m/%d"),
                        "Cumulative total": elem["tests_total"],
                    }
                )
        return pd.DataFrame(records)

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.pipe(self.pipe_metadata)
        return df

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Cuba().export()
