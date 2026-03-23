from datetime import datetime
import tempfile

import pandas as pd
import requests

from cowidev.testing import CountryTestBase


def read_xlsx_from_url(url, **kwargs):
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux i686)"}
    response = requests.get(url, headers=headers)
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        with open(tmp.name, "wb") as f:
            f.write(response.content)
        df = pd.read_excel(tmp.name, **kwargs)
    df = df.dropna(how="all")
    return df


class Germany(CountryTestBase):
    location: str = "Germany"
    source_url: str = "https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Daten/Testzahlen-gesamt.xlsx?__blob=publicationFile"

    def read(self):
        df = read_xlsx_from_url(self.source_url, sheet_name="1_Testzahlerfassung")
        mask = df.Kalenderwoche.str.match(r"\d{1,2}/\d{4}")
        df = df[mask]
        return df

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.assign(
            **{
                "Date": df.Kalenderwoche.apply(
                    lambda x: datetime.strptime(x + " +0", "%V/%G +%w").strftime("%Y-%m-%d")
                ),
                "Cumulative total": df["Anzahl Testungen"].cumsum(),
                "Positive rate": (df["Positivenanteil (%)"] / 100).round(3),
                "Source URL": self.source_url,
                "Source label": "Robert Koch Institut",
                "Units": "tests performed",
                "Country": self.location,
                "Notes": pd.NA,
            }
        ).sort_values("Date")

        df = df[
            [
                "Date",
                "Cumulative total",
                "Positive rate",
                "Source URL",
                "Source label",
                "Units",
                "Country",
                "Notes",
            ]
        ]
        return df

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Germany().export()
