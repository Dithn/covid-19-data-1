import re

import pandas as pd
import tabula

from cowidev.utils.web import request_json
from cowidev.utils.clean import clean_count, extract_clean_date
from cowidev.utils.utils import check_known_columns
from cowidev.vax.utils.base import CountryVaxBase


class Nepal(CountryVaxBase):
    location: str = "Nepal"
    source_url: dict = {
        "api": "https://covid19.mohp.gov.np/covid/api/ministryrelease",
        "base": "https://covid19.mohp.gov.np/covid/englishSituationReport/",
    }
    source_url_ref: dict = {
        "main": "https://covid19.mohp.gov.np/situation-report",
    }
    regex: dict = {
        "date": r"(\d{1,2}\-\d{1,2}\-20\d{2})",
        "count": r"\d+",
    }

    def read(self) -> tuple:
        """Reads data from source."""
        links = request_json(self.source_url["api"])
        df_main, df_manufacturer = self._parse_data(links)
        return df_main, df_manufacturer

    def _parse_data(self, links: dict) -> tuple:
        """Parses data from link."""
        # Obtain pdf url
        href = links["data"][0]["english_file"]
        self.source_url_ref["manufacturer"] = "{}{}".format(self.source_url["base"], href)
        # Extract table data
        df = self._parse_pdf_table()
        # Clean data
        df_main, df_manufacturer = self._parse_metrics(df)
        return df_main, df_manufacturer

    def _parse_pdf_table(self) -> pd.Series:
        """Extract table from pdf url"""
        # print(self.source_url_ref["manufacturer"])
        df_list = tabula.read_pdf(self.source_url_ref["manufacturer"], pages="all", stream=True, silent=True)
        df = [table for table in df_list if "Pfizer" in table.columns][0]
        # Checks data
        check_known_columns(
            df,
            [
                "Unnamed: 0",
                "Covid Shield",
                "Unnamed: 1",
                "Verocell",
                "Unnamed: 2",
                "J & J",
                "Pfizer",
                "Unnamed: 3",
                "Unnamed: 4",
                "Unnamed: 5",
                "Moderna",
                "Unnamed: 6",
            ],
        )
        return df[df["Unnamed: 0"] == "Total"].drop(columns=["Unnamed: 0"])

    def _parse_metrics(self, ds: pd.Series) -> tuple:
        """Parses metrics from data."""
        # Extract data
        count_list = self.extract_clean_count_series(ds, self.regex["count"])
        assert (
            len(count_list) == 14
        ), "New column is added in the table, please update the script. Number of columns: {}".format(len(count_list))
        # Create main variables
        total_vaccinations = sum(count_list)
        people_vaccinated = count_list[0] + count_list[3] + count_list[6] + count_list[8] + count_list[11]
        people_fully_vaccinated = count_list[1] + count_list[4] + count_list[6] + count_list[9] + count_list[12]
        total_boosters = count_list[2] + count_list[5] + count_list[7] + count_list[10] + count_list[13]
        # Create manufacturer variables
        covishield = count_list[0] + count_list[1] + count_list[2]
        verocell = count_list[3] + count_list[4] + count_list[5]
        jandj = count_list[6] + count_list[7]
        pfizer = count_list[8] + count_list[9] + count_list[10]
        moderna = count_list[11] + count_list[12] + count_list[13]
        # Create main dataseries
        df_main = {
            "total_vaccinations": [total_vaccinations],
            "people_vaccinated": [people_vaccinated],
            "people_fully_vaccinated": [people_fully_vaccinated],
            "total_boosters": [total_boosters],
        }
        # Create manufacturer dataframe
        df_manufacturer = {
            "total_vaccinations": [covishield, verocell, jandj, pfizer, moderna],
        }
        return pd.DataFrame(df_main), pd.DataFrame(df_manufacturer)

    def extract_clean_count_series(self, df: pd.DataFrame, regex: str) -> list:
        """Extracts clean count from series using regex."""
        count = []
        for cell in df.values.tolist()[0]:
            for text in cell.split():
                count.append(re.findall(self.regex["count"], text))
        count = [clean_count(item) for sublist in count for item in sublist]
        return count

    def _parse_date(self, link: str) -> str:
        """Get date from link."""
        return extract_clean_date(link, self.regex["date"], "%d-%m-%Y")

    def pipe_manufacturer_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes date for manufacturer data."""
        return df.assign(date=self._parse_date(self.source_url_ref["manufacturer"]))

    def pipe_manufacturer_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes vaccine names for manufacturer data."""
        return df.assign(
            **{"vaccine": ["Oxford/AstraZeneca", "Sinopharm/Beijing", "Johnson&Johnson", "Pfizer/BioNTech", "Moderna"]}
        )

    def pipe_manufacturer_location(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes location for manufacturer data."""
        return df.assign(location=self.location)

    def pipeline_manufacturer(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for manufacturer data."""
        return (
            df.pipe(self.pipe_manufacturer_date)
            .pipe(self.pipe_manufacturer_vaccine)
            .pipe(self.pipe_manufacturer_location)
        )

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes date for main data."""
        return df.assign(date=self._parse_date(self.source_url_ref["manufacturer"]))

    def pipe_location(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes location for main data."""
        return df.assign(location=self.location)

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes vaccine names for main data."""
        return df.assign(vaccine="Johnson&Johnson, Moderna, Oxford/AstraZeneca, Pfizer/BioNTech, Sinopharm/Beijing")

    def pipe_source(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes source for main data."""
        return df.assign(source_url=self.source_url_ref["main"])

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for main data."""
        return df.pipe(self.pipe_date).pipe(self.pipe_location).pipe(self.pipe_vaccine).pipe(self.pipe_source)

    def export(self):
        """Exports data to CSV."""
        df_main, df_manufacturer = self.read()
        # Pipelines
        df_main = df_main.pipe(self.pipeline)
        df_manufacturer = df_manufacturer.pipe(self.pipeline_manufacturer)
        # Export to CSV
        self.export_datafile(
            df=df_main,
            df_manufacturer=df_manufacturer,
            attach=True,
            attach_manufacturer=True,
            meta_manufacturer={
                "source_name": "Ministry of Health and Population",
                "source_url": self.source_url_ref["main"],
            },
        )


def main():
    Nepal().export()
