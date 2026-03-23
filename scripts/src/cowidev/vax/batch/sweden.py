

import pandas as pd

from cowidev.utils import get_soup
from cowidev.utils.clean import clean_date, clean_date_series
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.utils import build_vaccine_timeline, make_monotonic
from cowidev.utils.web.download import read_xlsx_from_url


# TODO: change source: https://www.fohm.se/folkhalsorapportering-statistik/statistikdatabaser-och-visualisering/vaccinationsstatistik/statistik-for-vaccination-mot-covid-19/
class Sweden(CountryVaxBase):
    def __init__(self):
        """Constructor."""
        self.source_url = "https://www.fohm.se/folkhalsorapportering-statistik/statistikdatabaser-och-visualisering/vaccinationsstatistik/statistik-for-vaccination-mot-covid-19/"
        self._base_url = "https://www.fohm.se"
        self.location = "Sweden"
        self.columns_rename = None

    def get_file_url(self):
        soup = get_soup(self.source_url)
        # Find html element with downloadable url
        elem_xlsx = soup.find_all(class_="xlsx")
        assert len(elem_xlsx) == 1, "More than one downloadable XLSX file was found!"
        # Build URL
        suffix = elem_xlsx[0].get("href")
        url_file = f"{self._base_url}{suffix}"
        return url_file

    def read(self) -> pd.DataFrame:
        url = self.get_file_url()
        dfs = read_xlsx_from_url(url, sheet_name=None)
        return dfs["1. Vaccinationer tidsserie"]


    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_date)
            .pipe(self.pipe_vaccine)
            .pipe(self.pipe_filter_rows)
            .pipe(self.pipe_columns)
            # .pipe(self.pipe_out_columns)
            # .pipe(self.pipe_add_boosters)
            .pipe(self.pipe_merge_with_archived)
            .pipe(make_monotonic)
            .drop_duplicates(subset=["date"], keep=False)
        )

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Read weekly data

        This data is loaded from an excel. It contains very clean (but sparse, i.e. weekly) data.
        """
        # Get date
        df["date"] = df["År"].astype(str) + "W" + df["Vecka"].astype(str)
        df["date"] = clean_date_series(df["date"] + "+1", "%GW%V+%w")
        # Drop unused columns
        df = df.drop(columns=["Vecka", "År"]).sort_values("date")
        # print(df)
        return df

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        # Source: https://www.ecdc.europa.eu/en/publications-data/data-covid-19-vaccination-eu-eea
        return build_vaccine_timeline(
            df,
            {
                "Pfizer/BioNTech": "2021-01-01",
                "Moderna": "2021-01-15",
                "Oxford/AstraZeneca": "2021-02-12",
                "Novavax": "2022-03-11",
            },
        )

    def pipe_filter_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df[df["Region"]=="| Sverige |"]
        return df


    def pipe_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df["total_vaccinations"] = df.sort_values("date")["Antal vaccinationer"]
        df = df.drop(columns=["Region", "Antal vaccinationer"])
        return df.assign(location=self.location, source_url=self.source_url)

    def pipe_merge_with_archived(self, df: pd.DataFrame) -> pd.DataFrame:
        df_archived = self.load_archived_data()
        df = df[df["date"] > df_archived["date"].max()]
        df = pd.concat([df_archived, df], ignore_index=True).sort_values(["date"])
        return df

    def pipe_out_columns(self, df: pd.DataFrame):
        return df[
            [
                "date",
                "location",
                "source_url",
                "vaccine",
                "total_vaccinations",
                "people_vaccinated",
                "people_fully_vaccinated",
                "total_boosters",
            ]
        ]


    def export(self):
        """Generalized."""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Sweden().export()
