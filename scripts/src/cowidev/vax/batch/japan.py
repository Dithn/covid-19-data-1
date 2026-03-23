"""This script is very complex and should be re-written from scratch."""
from datetime import datetime

import pandas as pd
import numpy as np
from bs4 import BeautifulSoup

from cowidev.utils.clean import clean_date_series, clean_df_columns_multiindex
from cowidev.utils.web.scraping import get_response
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.checks import validate_vaccines
from cowidev.vax.utils.utils import build_vaccine_timeline


class Japan(CountryVaxBase):
    location: str = "Japan"
    source_name: str = "Prime Minister's Office"
    # URL to early data
    source_url_early: str = "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/vaccine_sesshujisseki.html"
    # URL to latest data
    source_url_latest: str = "https://www.kantei.go.jp/jp/content/vaccination_data5.xlsx"
    source_url_latest_bst: str = "https://www.kantei.go.jp/jp/content/allbooster_data.xlsx"
    # Reference URL
    source_url_ref: str = "https://www.kantei.go.jp/jp/headline/kansensho/vaccine.html"

    age_groups_bst: dict = {"all": ["すべて"], "65-": ["うち高齢者"], "5-11": ["うち小児接種"]}
    age_group_remain: str = "12-64"
    # Formatting of the sheets ()
    sheets_bst: dict = {
        "総接種回数": None,
        "一般接種": {"name": "general", "header": [1, 2], "date": "接種日", "ind": age_groups_bst},
        "職域接種": {"name": "workplace", "header": [2, 3], "date": "集計日", "ind": ["接種回数"]},
        "重複": {"name": "overlap", "header": [2, 3], "date": "公表日", "ind": ["接種回数"]},
    }

    sheets_bst2: dict = {
        "総接種回数": None,
        "一般接種": {
            "name": "general",
            "header": [1, 2, 3, 4],
            "date": "接種日",
            "ind": ["曜日", "すべて", ""],
        },
    }
    metrics_bst: dict = {"dose3": []}
    metrics_bst2: dict = {"dose4": []}
    metrics_age: dict = {
        "dose1": "people_vaccinated",
        "dose2": "people_fully_vaccinated",
        "dose3": "people_with_booster",
    }
    vaccine_mapping: dict = {
        "ファイザー社": "Pfizer/BioNTech",
        "モデルナ社": "Moderna",
        "アストラゼネカ社": "Oxford/AstraZeneca",
        "武田社(ノババックス)": "Novavax",
        "武田社\n(ノババックス)": "Novavax",
        "接種回数(合計)": None,
        "ファイザー社\n(BA.1)": "Pfizer/BioNTech",
        "モデルナ社\n(BA.1)": "Moderna",
        "ファイザー社\n(BA.4-5)": "Pfizer/BioNTech",
        "モデルナ社\n(BA.4-5)": "Moderna",
    }

    # To be removed
    source_url_bst: str = "https://www.kantei.go.jp/jp/content/booster_data.xlsx"
    source_url_bst2: str = "https://www.kantei.go.jp/jp/content/booster2nd_data.xlsx"

    def read(self) -> pd.DataFrame:
        df_early = self.read_early().pipe(self.pipe_read_early)
        df_latest = self.read_latest().pipe(self.pipe_read_latest)
        return pd.concat([df_early, df_latest]).reset_index(drop=True)

    def read_early(self) -> pd.DataFrame:
        # Early data reported in static HTML page
        soup = BeautifulSoup(get_response(self.source_url_early).content, "lxml")
        dfs = pd.read_html(str(soup), header=0)
        assert len(dfs) == 1, f"Only one table should be present. {len(dfs)} tables detected."
        return dfs[0]

    def pipe_read_early(self, df: pd.DataFrame) -> pd.DataFrame:
        # Filter columns & rows
        cols_early: dict = {
            "日付": "date",
            "内１回目": "dose1",
            "内２回目": "dose2",
        }
        df = df[cols_early.keys()].rename(columns=cols_early)
        df = df[df.date != "合計"]
        return df.assign(
            date=clean_date_series(df.date),
            age_group="all",
            vaccine="Pfizer/BioNTech",
            source_url=self.source_url_early,
        ).sort_values("date")

    def read_latest(self) -> pd.DataFrame:
        dfs = [
            self._read_latest_main(),
            self._read_latest_booster(),
        ]
        # dfs.append(self._read_xlsx(self.source_url_bst, self.sheets_bst, self.metrics_bst))
        # dfs.append(self._read_xlsx(self.source_url_bst2, self.sheets_bst2, self.metrics_bst2))

        # Get rid of 'overlap' sheet
        dfs = [df for dfs_ in dfs for name, df in dfs_.items() if "overlap" not in name]
        return pd.concat(dfs).reset_index(drop=True)

    def _read_latest_main(self) -> pd.DataFrame:
        """Read data from excel main file."""
        metrics_in_overlap = {"dose1": ["内1回目"], "dose2": ["内2回目"]}
        sheets_format = {
            "総接種回数": None,
            "初回接種_一般接種": {
                "name": "general",
                "header": [2, 3, 4],
                "date": "接種日",
                "ind": {
                    "all": ["すべて"],
                    "65-": ["うち高齢者"],
                    "5-11": ["うち小児接種"],
                    "0-5": ["うち乳幼児接種"],
                },
                "metrics": metrics_in_overlap,
            },
            "初回接種_医療従事者等": {
                "name": "healthcare",
                "header": [2, 3],
                "date": "集計日",
                "ind": [],
                "metrics": metrics_in_overlap,
            },
            "初回接種_職域接種": {
                "name": "workplace",
                "header": [2, 3],
                "date": "集計日",
                "ind": [],
                "metrics": metrics_in_overlap,
            },
            "初回接種_重複": {
                "name": "overlap",
                "header": [2, 3],
                "date": "公表日",
                "ind": [],
                "metrics": metrics_in_overlap,
            },
        }
        df = self._read_xlsx(
            url=self.source_url_latest, sheets_format=sheets_format, metrics_in_overlap=metrics_in_overlap
        )
        return df

    def _read_latest_booster(self) -> pd.DataFrame:
        """Read data from excel main file (only booster data)."""
        metrics_in_overlap = {"dose3": []}
        sheets_format = {
            "３回目_総接種回数": None,
            "３回目_一般接種回数": {
                "name": "general_3",
                "header": [1, 2],
                "date": "接種日",
                "ind": {
                    "all": ["すべて"],
                    "65-": ["うち高齢者"],
                    "5-11": ["うち小児接種"],
                    "0-5": ["うち乳幼児接種"],
                },
                "metrics": {"dose3": []},
            },
            "３回目_職域接種": {
                "name": "workplace_3",
                "header": [2, 3],
                "date": "集計日",
                "ind": ["接種回数"],
                "metrics": {"dose3": []},
            },
            "３回目_重複": {
                "name": "overlap_3",
                "header": [2, 3],
                "date": "集計日",
                "ind": ["接種回数"],
                "metrics": {"dose3": []},
            },
            "４回目_総接種回数": None,
            "４回目_一般接種回数": {
                "name": "general_4",
                "header": [0],
                "date": "接種日",
                "fct": _fix_general_4,
                "ind": {
                    "all": ["すべて"],
                    "65-": ["うち高齢者(65歳以上)"],
                    "5-11": ["うち小児接種"],
                },
                "metrics": {"dose4": []},
            },
            "オミクロン株対応ワクチン_総接種回数": None,
            "オミクロン株対応ワクチン_一般接種（３回目）": None,
            "オミクロン株対応ワクチン_一般接種（４回目）": None,
            "オミクロン株対応ワクチン_一般接種（５回目）": {
                "name": "general_5",
                "header": [1, 2],
                "date": "接種日",
                "ind": {
                    "all": ["すべて"],
                    "65-": ["うち高齢者(65歳以上)"],
                },
                "metrics": {"dose5": []},
            },
        }
        df = self._read_xlsx(
            url=self.source_url_latest_bst,
            sheets_format=sheets_format,
            metrics_in_overlap=metrics_in_overlap,
            col_workplace="workplace_3",
            col_overlap="overlap_3",
        )
        return df

    def _read_xlsx(
        self,
        url: str,
        sheets_format: dict,
        metrics_in_overlap: dict,
        col_workplace: str = "workplace",
        col_overlap: str = "overlap",
    ) -> dict:
        # Download excel
        xlsx = pd.ExcelFile(url)
        # Check Excel sheets are as expected
        sheets_unknown = set(xlsx.sheet_names) - set(sheets_format.keys())
        if sheets_unknown:
            raise ValueError(f"Unknown sheets: {sheets_unknown}")
        # Build dfs
        dfs = {}
        for sheet_name, formatting in sheets_format.items():
            if formatting:
                # Change sheet name, set headers
                df = xlsx.parse(sheet_name=sheet_name, header=formatting["header"]).dropna(how="all", axis=0)
                # Fixes
                if "fct" in formatting:
                    df = formatting["fct"](df)
                # Parse dataframe (date, age group namings, etc.)
                if isinstance(formatting["ind"], dict):
                    dfs_ = []
                    for age_group, ind in formatting["ind"].items():
                        df_ = self._parse_df(df, formatting["date"], ind, formatting["metrics"])
                        dfs_.append(df_.assign(age_group=age_group))
                    dfs[formatting["name"]] = pd.concat(dfs_).reset_index(drop=True)
                else:
                    df_ = self._parse_df(df, formatting["date"], formatting["ind"], formatting["metrics"]).assign(
                        age_group="all"
                    )
                    dfs[formatting["name"]] = df_

        if isinstance(dfs.get(col_workplace), pd.DataFrame):
            # Estimate daily metrics for workplace data based on the latest overlap data
            for metric in metrics_in_overlap.keys():
                workplace_latest = dfs[col_workplace][metric].iat[-1]
                overlap_latest = dfs[col_overlap][metric].iat[-1]
                dfs[col_workplace][metric] -= dfs[col_workplace][metric].shift(1, fill_value=0)
                dfs[col_workplace][metric] *= 1 - overlap_latest / workplace_latest
        return dfs

    def _parse_df(self, df: pd.DataFrame, date_col: str, ind: list, metrics: dict) -> pd.DataFrame:
        # Clean columns
        df = clean_df_columns_multiindex(df.dropna(axis=1, how="all"))
        df = df.loc[:, ~df.columns.duplicated()]
        # Filter and clean metric rows
        df = df[df[date_col].apply(isinstance, args=(datetime,)) & df[date_col].notna()]
        df[date_col] = clean_date_series(df[date_col])
        df = df.set_index(date_col).sort_index()
        dfs = []
        for metric, index in metrics.items():
            # Get, check, convert and rename metric columns
            df_ = df[tuple(ind + index)]
            if isinstance(df_, pd.Series):
                df_ = pd.DataFrame(df_)
                df_ = df_.rename(columns={"すべて": 0})
            df_ = df_.stack().reset_index()
            cols_unknown = set(df_.columns) - {date_col, "level_1", 0}
            if cols_unknown:
                raise ValueError(f"Unknown columns: {cols_unknown}, {df_.columns}")
            df_[0] = pd.to_numeric(df_[0], errors="coerce")
            dfs.append(df_.rename(columns={date_col: "date", "level_1": "vaccine", 0: metric}))
        while len(dfs) > 1:
            dfs[0] = dfs[0].merge(dfs.pop(1), on=["date", "vaccine"])
        return dfs[0]

    def pipe_read_latest(self, df: pd.DataFrame) -> pd.DataFrame:
        # Check and map vaccine names
        validate_vaccines(df, self.vaccine_mapping)
        df = df.fillna(0).replace(self.vaccine_mapping).dropna()
        # Aggregate metrics by the same date & age group & vaccine
        df = df.groupby(["date", "age_group", "vaccine"], as_index=False).sum()
        return df.assign(source_url=self.source_url_ref)

    def pipeline_base(self, df: pd.DataFrame) -> pd.DataFrame:
        # Get cumulative metrics
        metrics = df.filter(like="dose").columns
        df[metrics] = df.fillna(0).groupby(["age_group", "vaccine"])[metrics].cumsum().round()
        df["total_vaccinations"] = df[metrics].sum(axis=1)
        return df[df.total_vaccinations > 0].assign(location=self.location)

    def pipeline_age(self, df: pd.DataFrame) -> pd.DataFrame:
        metrics = list(self.metrics_age.keys())
        df = df.groupby(["date", "age_group", "location"], as_index=False)[metrics].sum()
        # Get the remaining age group
        df_all = df[df.age_group == "all"].set_index("date")
        df_groups = df[df.age_group != "all"]
        df_groups_sum = df_groups.groupby("date").sum()
        df_all[metrics] = df_all[metrics].sub(df_groups_sum[metrics], fill_value=0)
        df_remain = df_all.reset_index().assign(age_group=self.age_group_remain)
        df = pd.concat([df_groups, df_remain]).reset_index(drop=True)
        # Parse age groups, rename metric columns and calculate per capita metrics
        df[["age_group_min", "age_group_max"]] = df.age_group.str.split("-", expand=True)
        return df.rename(columns=self.metrics_age).pipe(self.pipe_age_per_capita)

    def pipeline_manufacturer(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df.age_group == "all"][["location", "date", "vaccine", "total_vaccinations"]]

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df["total_boosters"] = df.dose3 + df.dose4 + df.dose5
        return df.rename(columns={"dose1": "people_vaccinated", "dose2": "people_fully_vaccinated"})

    def pipe_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df[df.age_group == "all"]
        vaccine_timeline = df[["date", "vaccine"]].groupby("vaccine").min().date.to_dict()
        df = df.groupby(["date", "location", "source_url"], as_index=False).agg(
            {
                "total_vaccinations": "sum",
                "people_vaccinated": "sum",
                "people_fully_vaccinated": "sum",
                "total_boosters": "sum",
            }
        )
        return df.pipe(build_vaccine_timeline, vaccine_timeline)

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_metrics)
            .pipe(self.pipe_aggregate)
            .pipe(self.make_monotonic)[
                [
                    "location",
                    "date",
                    "vaccine",
                    "source_url",
                    "total_vaccinations",
                    "people_vaccinated",
                    "people_fully_vaccinated",
                    "total_boosters",
                ]
            ]
        )

    def export(self):
        # Read and preprocess
        df = self.read().pipe(self.pipeline_base)
        # Transform
        df_age = df.pipe(self.pipeline_age)
        df_man = df.pipe(self.pipeline_manufacturer)
        df = df.pipe(self.pipeline)
        # Export
        self.export_datafile(
            df=df,
            df_age=df_age,
            df_manufacturer=df_man,
            meta_age={"source_name": self.source_name, "source_url": self.source_url_ref},
            meta_manufacturer={"source_name": self.source_name, "source_url": self.source_url_ref},
        )


def main():
    Japan().export()


def _fix_general_4(df: pd.DataFrame):
    # Assert expected format
    assert (
        pd.isnull(df.loc[0, "Unnamed: 2"])
        and (df.loc[1, "Unnamed: 2"] == "すべて")
        and pd.isnull(df.loc[0, "Unnamed: 6"])
        and (df.loc[1, "Unnamed: 6"] == "うち60歳以上")
        and pd.isnull(df.loc[0, "Unnamed: 9"])
        and pd.isnull(df.loc[1, "Unnamed: 9"])
        and (df.loc[2, "Unnamed: 9"] == "うち高齢者（65歳以上）")
        and pd.isnull(df.loc[0, df.columns[-1]])
        and (df.loc[1, df.columns[-1]] == "うち小児接種")
    )
    # Shift row values up
    df.loc[[0, 1], "Unnamed: 2"] = ["すべて", np.nan]
    df.loc[[0, 2], "Unnamed: 9"] = ["うち高齢者（65歳以上）", np.nan]
    df.loc[[0, 1], df.columns[-1]] = ["うち小児接種", np.nan]
    df = df.drop(columns=["Unnamed: 6", "Unnamed: 7", "Unnamed: 8"])
    # Remove all-NaN rows
    df = df.dropna(how="all", axis=0)
    # Set header
    df.columns = pd.MultiIndex.from_arrays(df.iloc[0:2].ffill(axis=1).values)
    df = df.iloc[2:]
    return df
