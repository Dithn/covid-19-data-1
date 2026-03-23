import pandas as pd

from datetime import datetime
from dateutil.relativedelta import relativedelta, TU

from cowidev.utils.clean.dates import clean_date_series
from cowidev.testing import CountryTestBase


class CostaRica(CountryTestBase):
    location = "Costa Rica"
    units = "people tested"
    source_url_ref = "https://geovision.uned.ac.cr/oges/"
    source_label = "Ministry of Health"

    def read(self):
        df = pd.read_csv(self.source_url, delimiter=";", usecols=["nue_posi", "conf_nexo", "nue_descar", "FECHA"])
        return df

    @property
    def source_url(self):
        dt1 = (datetime.now() + relativedelta(weekday=TU(-1))).strftime("%Y_%m_%d")
        dt2 = (datetime.now() + relativedelta(weekday=TU(-1))).strftime("%m_%d_%y")
        return f"https://geovision.uned.ac.cr/oges/archivos_covid/{dt1}/{dt2}_CSV_GENERAL.csv"

    def pipe_date(self, df: pd.DataFrame):
        return df.assign(Date=clean_date_series(df["FECHA"], format_input="%d/%m/%Y"))

    def pipe_aggregate(self, df: pd.DataFrame):
        df = df[~df.nue_descar.isin(["nd"])]
        df = df.assign(
            # nue_posi=pd.to_numeric(df["nue_posi"], errors="coerce"),
            # conf_nexo=pd.to_numeric(df["conf_nexo"], errors="coerce"),
            nue_descar=pd.to_numeric(df["nue_descar"], errors="coerce"),
        )
        return df.groupby("Date", as_index=False).sum()

    def pipe_metrics(self, df: pd.DataFrame):
        lab_pos = df.nue_posi.fillna(0) - df.conf_nexo.fillna(0)
        df = df.assign(**{"Daily change in cumulative total": lab_pos.fillna(0) + df.nue_descar.fillna(0)})
        df = df[df["Daily change in cumulative total"] != 0]
        df["Positive rate"] = (
            lab_pos.rolling(7).sum() / df["Daily change in cumulative total"].rolling(7).sum()
        ).round(3)
        return df.sort_values("Date")

    def pipeline(self, df: pd.DataFrame):
        df = df.pipe(self.pipe_date)
        df = df.pipe(self.pipe_aggregate)
        df = df.pipe(self.pipe_metrics)
        df = df.pipe(self.pipe_metadata)
        return df

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, reset_index=True)


def main():
    CostaRica().export()
