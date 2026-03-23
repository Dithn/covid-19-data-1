import re
import json

import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.utils.web import get_soup
from cowidev.utils.clean import clean_date_series, clean_count


class Iceland(CountryTestBase):
    location: str = "Iceland"
    units: str = "tests performed"
    source_label: str = "Government of Iceland"
    source_url_ref: str = "https://www.covid.is/data"
    source_url: str = "https://e.infogram.com/"
    regex: dict = {
        "title_test": r"Fjöldi sýna eftir dögum",
        "title_positive": r"Fjöldi smita innanlands",
        "element": r"window\.infographicData=({.*})",
    }
    rename_columns: dict = {
        "Symptomatic tests": "t1",
        "Sympotmatic tests": "t1",
        "PCR domestic tests": "t1",
        "Domestic tests (PCR or antigen)": "t1",
        "Antigen domestic tests": "t2",
        "Quarantine- and random tests": "t2",
        "deCODE Genetics screening": "t3",
        "Border tests 1 and 2": "t4",
        "Border tests": "t4",
        "Domestic infections (PCR or antigen test)": "p1",
        "Domestic infections": "p1",
        "Symptomatic screening": "p1",
        "Domestic infections PCR": "p2",
        "Quarantine- and random screening": "p2",
        "Screening by deCODE Genetics": "p3",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        data_id = self._get_data_id_from_source(self.source_url_ref)
        data = self._load_data(data_id)
        df = self._build_df(data)
        return df

    def _get_data_id_from_source(self, source_url: str) -> str:
        """Get Data ID from source"""
        soup = get_soup(source_url)
        data_id = soup.find(class_="infogram-embed")["data-id"]
        return data_id

    def _load_data(self, data_id):
        """Load data from source"""
        url = f"{self.source_url}{data_id}"
        soup = get_soup(url)
        match = re.search(self.regex["element"], str(soup))
        if not match:
            raise ValueError("Website Structure Changed, please update the script")
        data = json.loads(match.group(1))
        return data

    def _build_df(self, data: dict) -> pd.DataFrame:
        """Create dfs from raw data"""
        data = data["elements"]["content"]["content"]["entities"]
        data_test = [v for v in data.values() if re.search(self.regex["title_test"], str(v))][0]
        data_positive = [v for v in data.values() if re.search(self.regex["title_positive"], str(v))][0]

        d = {}
        for iteration, item in enumerate(data_test["props"]["chartData"]["data"]):
            test_list = data_test["props"]["chartData"]["data"][iteration]
            d["df" + str(iteration)] = pd.DataFrame(test_list, columns=test_list[0]).drop(0)
            d["df" + str(iteration)] = d[("df" + str(iteration))][d[("df" + str(iteration))].iloc[:, 0] != ""]
            d["df" + str(iteration)].columns = d["df" + str(iteration)].columns.fillna("")
        tests = pd.concat(d.values(), ignore_index=True)

        p = {}
        for iteration, item in enumerate(data_positive["props"]["chartData"]["data"]):
            pos_list = data_positive["props"]["chartData"]["data"][iteration]
            p["df" + str(iteration)] = pd.DataFrame(pos_list, columns=pos_list[0]).drop(0)
            p["df" + str(iteration)] = p[("df" + str(iteration))][p[("df" + str(iteration))].iloc[:, 0] != ""]
            p["df" + str(iteration)].columns = p["df" + str(iteration)].columns.fillna("")
        pos = pd.concat(p.values(), ignore_index=True)

        return pd.merge(tests, pos)

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean date"""
        return df.assign(Date=clean_date_series(df.iloc[:, 0], "%d.%m.%y")).sort_values("Date")

    def pipe_row_sum(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sum rows"""
        df["Daily change in cumulative total"] = df[["t1", "t2", "t3"]].applymap(clean_count).sum(axis=1)
        df["positive"] = df[["p1", "p2", "p3"]].applymap(clean_count).sum(axis=1)
        return df.drop_duplicates(subset="Date")

    def pipe_pr(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Positive Rate"""
        df["Positive rate"] = (
            (df["positive"].rolling(7).sum().div(df["Daily change in cumulative total"].rolling(7).sum())).fillna(0)
        ).round(3)
        return df

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data processing"""
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_date)
            .pipe(self.pipe_row_sum)
            .pipe(self.pipe_pr)
            .pipe(self.pipe_metadata)
        )

    def export(self):
        """Export data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, float_format="%.5f")


def main():
    Iceland().export()
