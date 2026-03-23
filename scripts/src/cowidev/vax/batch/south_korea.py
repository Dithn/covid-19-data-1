import pandas as pd

from cowidev.utils.clean import clean_date_series
from cowidev.vax.utils.checks import VACCINES_ONE_DOSE
from cowidev.vax.utils.utils import build_vaccine_timeline
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.utils.web.download import to_proxy_url


class SouthKorea(CountryVaxBase):
    def __init__(self):
        self.location = "South Korea"
        self.source_url = "https://ncv.kdca.go.kr/vaccineStatus.es?mid=a11710000000"
        self.source_url_ref = "https://ncv.kdca.go.kr/"
        self.vaccines_mapping = {
            "모더나": "Moderna",
            "아스트라제네카": "Oxford/AstraZeneca",
            "화이자": "Pfizer/BioNTech",
            "얀센": "Johnson&Johnson",
            "노바백스": "Novavax",
            "스카이코비원": "SKYCovione",
            # "전체": "all",
            # "일자": "date",
            # "기타": "other",
        }
        self.rename_cols_lv0 = {
            "전체": "all",
            "기타": "others",
            "일자": "date",
            **self.vaccines_mapping,
        }
        self.rename_cols_lv1 = {
            "1·2차": "dose_1",
            "1차": "dose_1",
            "2차": "dose_2",
            "3차": "dose_3",
            "4차": "dose_4",
            "일자": "date",
        }

    def read(self):
        # alternative would be to use `headers` in requests.get
        dfs = pd.read_html(to_proxy_url(self.source_url), encoding="utf-8")
        # dfs = pd.read_html(self.source_url, encoding="utf-8")
        if len(dfs) != 1:
            raise ValueError("More than one table detected!")
        df = dfs[0]
        return df

    def pipe_drop_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        # df = df.drop(columns=["동절기"], level=0)
        return df

    def pipe_rename_columns_raw(self, df: pd.DataFrame):
        # Check columns start
        columns_lv = {
            0: list(self.rename_cols_lv0.keys()),
            1: list(self.rename_cols_lv1.keys()),
        }
        self._check_format_multicols(df, columns_lv)
        df = df.rename(columns=self.rename_cols_lv0, level=0)
        df = df.rename(columns=self.rename_cols_lv1, level=1)
        # Check columns end
        columns_lv = {
            0: list(self.rename_cols_lv0.values()),
            1: list(self.rename_cols_lv1.values()),
        }
        self._check_format_multicols(df, columns_lv)
        return df

    def _check_format_multicols(self, df: pd.DataFrame, columns_lv) -> pd.DataFrame:
        columns_lv_wrong = {i: df.columns.get_level_values(i).difference(k) for i, k in columns_lv.items()}
        for lv, diff in columns_lv_wrong.items():
            if any(diff):
                raise ValueError(f"Unknown columns in level {lv}: {diff}")

    def pipe_check_metrics(self, df: pd.DataFrame):
        vaccines = list(self.vaccines_mapping.values()) + ["others"]
        # Uncomment when boosters are available
        for dose in ["dose_1", "dose_2"]:  # , "dose_3", "dose_4"]:
            d = 0
            # print(dose)
            for vaccine in vaccines:
                # print(vaccine)
                if (vaccine in VACCINES_ONE_DOSE) & (dose == "dose_2"):
                    d += df.loc[:, (vaccine, "dose_1")]
                else:
                    if dose in df.loc[:, vaccine].columns:
                        d += df.loc[:, (vaccine, dose)]
            # if not (d == df[("all", dose)]).all():
            if not ((df[("all", dose)] - d) / d).max() < 0.02:
                raise ValueError(f"Metric {dose} for 'all' is not equal to the sum over all vaccines (2% tolerance).")
        return df

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        df.loc[:, ("date", "date")] = clean_date_series(df[("date", "date")], format_input="'%y.%m.%d")
        return df

    def pipe_cumsum(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = [col for col in df.columns if col not in [("date", "date")]]
        df = df.sort_values(("date", "date")).drop_duplicates(subset=("date", "date"), keep="first")
        df.loc[:, cols] = df[cols].cumsum()
        return df

    def pipeline_base(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_drop_columns)
            .pipe(self.pipe_rename_columns_raw)
            .pipe(self.pipe_check_metrics)
            .pipe(self.pipe_date)
            .pipe(self.pipe_cumsum)
        )

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        one_dose_cols = [col for col in df.columns.levels[0] if col in VACCINES_ONE_DOSE]
        df = pd.DataFrame(
            {
                "date": df.loc[:, ("date", "date")],
                "people_vaccinated": df.loc[:, ("all", "dose_1")],
                "people_fully_vaccinated": df.loc[:, ("all", "dose_2")],
                # Uncomment when boosters are available
                # "total_boosters": df.loc[:, ("all", "dose_3")] + df.loc[:, ("all", "dose_4")],
                "single_doses": df.loc[:, (one_dose_cols, "dose_1")].sum(axis=1),
            }
        )
        # Uncomment when boosters are available
        # df = df.assign(
        #     total_vaccinations=(
        #         df["people_vaccinated"] + df["people_fully_vaccinated"] + df["total_boosters"] - df["single_doses"]
        #     )
        # )
        return df

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(
            source_url=self.source_url_ref,
            location=self.location,
        )

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        vax_timeline = {
            "Oxford/AstraZeneca": "2021-02-26",
            "Pfizer/BioNTech": "2021-02-27",
            "Moderna": "2021-06-18",
            "Johnson&Johnson": "2021-06-10",
            "Novavax": "2022-02-14",
        }
        return build_vaccine_timeline(df, vax_timeline)

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_metrics)
            .pipe(self.pipe_metadata)
            .pipe(self.pipe_vaccine)[
                [
                    "location",
                    "date",
                    "vaccine",
                    "source_url",
                    # Uncomment when boosters are available
                    # "total_vaccinations",
                    "people_vaccinated",
                    "people_fully_vaccinated",
                    # Uncomment when boosters are available
                    # "total_boosters",
                ]
            ]
            .sort_values("date")
            .drop_duplicates()
        )

    def pipe_man_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        data = {"date": df[("date", "date")]}
        for col in self.vaccines_mapping.values():
            data[col] = df[col].sum(axis=1)
        return pd.DataFrame(data)

    def pipe_man_melt(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.melt(id_vars="date", var_name="vaccine", value_name="total_vaccinations")

    def pipeline_manufacturer(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_man_aggregate)
            .pipe(self.pipe_man_melt)
            .assign(location=self.location)
            .sort_values(["date", "vaccine"])
            .reset_index(drop=True)
        )

    def export(self):
        df_base = self.read().pipe(self.pipeline_base)
        # Main data
        df = df_base.pipe(self.pipeline)
        # Vaccination by manufacturer
        df_man = df_base.pipe(self.pipeline_manufacturer)
        # Export
        self.export_datafile(
            df,
            df_manufacturer=df_man,
            meta_manufacturer={
                "source_name": "Korea Centers for Disease Control and Prevention",
                "source_url": self.source_url_ref,
            },
            merge=True,
        )


def main():
    SouthKorea().export()
