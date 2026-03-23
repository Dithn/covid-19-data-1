import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.utils import clean_date_series, clean_count
from cowidev.utils.web import request_json


class Colombia(CountryTestBase):
    location = "Colombia"
    units = "tests performed"
    source_url_ref = "https://www.ins.gov.co/Noticias/Paginas/coronavirus-pcr.aspx"
    source_label = "National Institute of Health"

    def _read_antigens(self):
        ## Antigen
        url = "https://atlas.jifo.co/api/connectors/425b93dc-c055-477c-b81a-5d4d9a1275f7"
        data = request_json(url)["data"][4]
        df = pd.DataFrame.from_records(data[1:], columns=data[0])
        # Clean
        df = df[df[""] != ""]
        df = df.assign(Date=clean_date_series(df[""], "%d/%m/%Y"))
        df["Positivas"] = df["Positivas"].apply(clean_count)
        df["Total Px Ag"] = df["Total Px Ag"].apply(clean_count)
        return df

    def _read_pcr(self):
        df = pd.read_csv(
            "https://www.datos.gov.co/resource/8835-5baf.csv",
            usecols=["fecha", "positivas_acumuladas", "negativas_acumuladas"],
        )
        df = df[(df["fecha"] != "Acumulado Feb") & (df.fecha.notnull())]
        df1 = df.loc[1:787].assign(Date=clean_date_series(df.loc[1:787]["fecha"], "%Y-%m-%dT%H:%M:%S.%f"))
        df2 = df.loc[788:].assign(Date=clean_date_series(df.loc[788:]["fecha"].str.extract(r"-(.*)")[0], "%d/%m/%Y"))
        df = df1.append(df2)
        # df = df.assign(Date=clean_date_series(df["fecha"], "%d/%m/%Y"))
        return df

    def read(self):
        ag = self._read_antigens()
        pcr = self._read_pcr()
        df = pd.merge(ag, pcr, how="outer").sort_values(by="Date")
        return df

    def pipe_cumulative_total(self, df: pd.DataFrame):
        df["Cumulative total"] = (
            df["positivas_acumuladas"]
            .fillna(0)
            .add(df["negativas_acumuladas"].fillna(0))
            .add(df["Total Px Ag"].fillna(0))
        )
        return df

    def pipe_positive_rate(self, df: pd.DataFrame):
        df["Positive total"] = df["positivas_acumuladas"].fillna(0).add(df["Positivas"].fillna(0))

        df = df[df["Cumulative total"] != 0]
        df = df[df["Cumulative total"] > df["Cumulative total"].shift(1)]
        df = df[df["Positive total"] != 0]

        df["Positive rate"] = (
            ((df["Positive total"] - df["Positive total"].shift(1)).rolling(7).mean())
            .div((df["Cumulative total"] - df["Cumulative total"].shift(1)).rolling(7).mean())
            .round(3)
        )
        return df

    def pipeline(self, df: pd.DataFrame):
        df = df.pipe(self.pipe_cumulative_total).pipe(self.pipe_positive_rate).pipe(self.pipe_metadata)
        return df

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, reset_index=True)


def main():
    Colombia().export()
