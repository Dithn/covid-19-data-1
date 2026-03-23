import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.testing.utils import make_monotonic
from cowidev.utils.web import get_soup
from cowidev.utils.clean import clean_date


class BosniaHerzegovina(CountryTestBase):
    location = "Bosnia and Herzegovina"
    source_url = [
        "http://mcp.gov.ba/publication/read/epidemioloska-slika-covid-19?pageId=3",
        "http://mcp.gov.ba/publication/read/epidemioloska-slika-novo?pageId=97",
    ]
    source_url_ref = ", ".join(source_url)
    source_label = "Ministry of Civil Affairs"
    units = "tests performed"

    def read(self):
        dfs = [self._load_data(url) for url in self.source_url]
        df = pd.concat(dfs)
        return df

    def _load_data(self, url: str):
        df = pd.DataFrame(self._get_records(url))
        df = df[~df["Cumulative total"].isna()]
        df = df.assign(**{"Source URL": url})
        return df

    def _get_records(self, url: str) -> dict:
        soup = get_soup(url)
        elem = soup.find(id="newsContent")
        elems = elem.find_all("table")
        records = [
            {
                "Date": self._parse_date(elem),
                "Cumulative total": self._parse_metric(elem),
            }
            for elem in elems
        ]
        return records

    def _parse_metric(self, elem):
        df = pd.read_html(str(elem), header=1)[0]
        value = df.loc[df["Unnamed: 0"] == "BiH", "Broj testiranih"].item()
        return value

    def _parse_date(self, elem):
        dt_raw = elem.find("p").text.strip()
        return clean_date(dt_raw, "%d.%m.%Y.")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.pipe(self.pipe_metadata).sort_values("Date")
        df.loc[:, "Cumulative total"] = (
            df.loc[:, "Cumulative total"].astype(str).str.replace(r"\s|\*", "", regex=True).astype(int)
        )
        df = df.pipe(self._remove_typo)
        df = df.drop_duplicates(subset="Date", keep=False)
        return df

    def _remove_typo(self, df: pd.DataFrame) -> pd.DataFrame:
        if (df.Date == "2021-01-08").sum() == 2:
            ds = abs(df.loc[df.Date == "2021-01-08", "Cumulative total"] - 535439)
            id_remove = ds.idxmax()
            df = df.drop(id_remove)
        df = df[df.Date != "2021-08-23"]
        return df

    def export(self):
        df = self.read().pipe(self.pipeline).pipe(make_monotonic)
        self.export_datafile(df)


def main():
    BosniaHerzegovina().export()
