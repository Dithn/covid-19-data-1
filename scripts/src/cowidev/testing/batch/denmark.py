import os
import tempfile
import pandas as pd

from cowidev.utils import clean_count, get_soup
from cowidev.utils.io import extract_zip
from cowidev.testing import CountryTestBase


class Denmark(CountryTestBase):
    location = "Denmark"
    source_url_ref = "https://covid19.ssi.dk/overvagningsdata/download-fil-med-overvaagningdata"
    units = "tests performed"
    source_label = "Statens Serum Institut"

    def read(self):
        url = self._parse_data_url()
        with tempfile.TemporaryDirectory() as tmp:
            extract_zip(url, tmp)
            return pd.read_csv(
                os.path.join(tmp, "Test_pos_over_time.csv"),
                delimiter=";",
                usecols=["Date", "Tested", "Tested_kumulativ"],
            )

    def _parse_data_url(self):
        soup = get_soup(self.source_url_ref)
        h3 = soup.find_all(class_="accordion-body")
        assert len(h3) == 4
        h5 = h3[1].find_all("h5")
        url = h5[0].a.get("href")
        return url

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.assign(
            **{
                "Daily change in cumulative total": df.Tested.apply(clean_count),
                "Cumulative total": df.Tested_kumulativ.apply(clean_count),
            }
        )
        df = df[df["Daily change in cumulative total"] != 0]
        return df

    def pipe_date(self, df: pd.DataFrame):
        msk = df.Date.str.match(r"20\d\d\-\d\d\-\d\d")
        return df[msk].sort_values("Date")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_metrics).pipe(self.pipe_date).pipe(self.pipe_metadata)

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Denmark().export()
