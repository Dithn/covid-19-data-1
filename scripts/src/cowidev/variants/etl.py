from datetime import timedelta, datetime

import pandas as pd

from cowidev import PATHS
from cowidev.utils.clean.dates import clean_date, DATE_FORMAT
from cowidev.utils.web import request_json
from cowidev import PATHS
from cowidev.utils.s3 import obj_to_s3


class VariantsETL:
    def __init__(self) -> None:
        self.source_url = (
            "https://raw.githubusercontent.com/hodcroftlab/covariants/master/web/public/data/perCountryData.json"
        )
        self.source_url_date = "https://github.com/hodcroftlab/covariants/raw/master/web/public/data/update.json"
        # CoVariants -> OWID name mapping. If who=False, variant is placed in bucket "non_who", along with "others"
        self.variants_details = {
            "20A.EU2": {"rename": "B.1.160", "who": False},
            "20A/S:439K": {"rename": "B.1.258", "who": False},
            "20A/S:98F": {"rename": "B.1.221", "who": False},
            "20B/S:1122L": {"rename": "B.1.1.302", "who": False},
            "20A/S:126A": {"rename": "B.1.620", "who": False},
            "20B/S:626S": {"rename": "B.1.1.277", "who": False},
            "20B/S:732A": {"rename": "B.1.1.519", "who": False},
            "20C/S:80Y": {"rename": "B.1.367", "who": False},
            "20E (EU1)": {"rename": "B.1.177", "who": False},
            "20H (Beta, V2)": {"rename": "Beta", "who": True},
            "20I (Alpha, V1)": {"rename": "Alpha", "who": True},
            "20J (Gamma, V3)": {"rename": "Gamma", "who": True},
            "21A (Delta)": {"rename": "Delta", "who": True},
            "21B (Kappa)": {"rename": "Kappa", "who": False},
            "21C (Epsilon)": {"rename": "Epsilon", "who": False},
            "21D (Eta)": {"rename": "Eta", "who": False},
            "21F (Iota)": {"rename": "Iota", "who": False},
            "21G (Lambda)": {"rename": "Lambda", "who": True},
            "21H (Mu)": {"rename": "Mu", "who": True},
            "21I (Delta)": {"rename": "Delta", "who": True},
            "21J (Delta)": {"rename": "Delta", "who": True},
            "21K (Omicron)": {"rename": "Omicron (BA.1)", "who": True},
            "21L (Omicron)": {"rename": "Omicron (BA.2)", "who": True},
            "22A (Omicron)": {"rename": "Omicron (BA.4)", "who": True},
            "22B (Omicron)": {"rename": "Omicron (BA.5)", "who": True},
            "22C (Omicron)": {"rename": "Omicron (BA.2.12.1)", "who": True},
            "22D (Omicron)": {"rename": "Omicron (BA.2.75)", "who": False},
            "22E (Omicron)": {"rename": "Omicron (BQ.1)", "who": True},
            "22F (Omicron)": {"rename": "Omicron (XBB)", "who": True},
            "23A (Omicron)": {"rename": "Omicron (XBB.1.5)", "who": True},
            "23B (Omicron)": {"rename": "Omicron (XBB.1.16)", "who": True},
            "23C (Omicron)": {"rename": "Omicron (CH.1.1)", "who": False},
            "23D (Omicron)": {"rename": "Omicron (XBB.1.9)", "who": True},
            "23E (Omicron)": {"rename": "Omicron (XBB.2.3)", "who": True},
            "23F (Omicron)": {"rename": "Omicron (EG.5.1)", "who": True},
            "23G (Omicron)": {"rename": "Omicron (XBB.1.5.70)", "who": True},
            "23H (Omicron)": {"rename": "Omicron (HK.3)", "who": True},
            "23I (Omicron)": {"rename": "Omicron (BA.2.86)", "who": True},
            "S:677H.Robin1": {"rename": "S:677H.Robin1", "who": False},
            "S:677P.Pelican": {"rename": "S:677P.Pelican", "who": False},
            "recombinant": {"rename": "Recombinant", "who": False},
        }
        self.country_mapping = {
            "USA": "United States",
            "Czech Republic": "Czechia",
            "Sint Maarten": "Sint Maarten (Dutch part)",
        }
        self.column_rename = {
            "total_sequences": "num_sequences_total",
        }
        self.columns_out = [
            "location",
            "date",
            "variant",
            "num_sequences",
            "perc_sequences",
            "num_sequences_total",
        ]
        self.num_sequences_total_threshold = 0

    @property
    def variants(self):
        return list(self.variants_details.keys())

    @property
    def variants_mapping(self):
        return {k: v["rename"] for k, v in self.variants_details.items()}

    @property
    def variants_who(self):
        return list(set(v["rename"] for v in self.variants_details.values() if v["who"]))

    def extract(self) -> dict:
        data = request_json(self.source_url)
        data = list(filter(lambda x: x["region"] == "World", data["regions"]))[0]["distributions"]
        return data

    @property
    def _parse_last_update_date(self):
        field_name = "lastUpdated"
        date_json = request_json(self.source_url_date)
        if field_name in date_json:
            date_raw = date_json[field_name]
            return datetime.fromisoformat(date_raw).date()
        raise ValueError(f"{field_name} field not found!")

    def transform(self, data: dict) -> pd.DataFrame:
        df = (
            self.json_to_df(data)
            .pipe(self.pipe_filter_by_num_sequences)
            .pipe(self.pipe_rename_columns)
            .pipe(self.pipe_variants)
            .pipe(self.pipe_filter_variants)
            .pipe(self.pipe_group_by_variants)
            .pipe(self.pipe_check_variants)
            .pipe(self.pipe_location)
            .pipe(self.pipe_date)
            .pipe(self.pipe_filter_locations)
            .pipe(self.pipe_variant_others)
            .pipe(self.pipe_variant_non_who)
            .pipe(self.pipe_dtypes)
            .pipe(self.pipe_percent)
            .pipe(self.pipe_correct_excess_percentage)
            .pipe(self.pipe_omicron)
            .pipe(self.pipe_out)
        )
        return df

    def transform_seq(self, df: pd.DataFrame) -> pd.DataFrame:
        df = (
            df.pipe(self.pipe_variant_dominant)
            .pipe(self.pipe_variant_totals)
            .pipe(self.pipe_per_capita)
            .pipe(self.pipe_cumsum)
        )
        return df

    def pipe_variant_dominant(self, df):
        # Remove Omicron (check dominant within sub-variants)
        df = df[df.variant != "Omicron"]
        # Rest of the code
        df = df.assign(variant=df.variant.replace({"non_who": "!non_who"}))
        df = df.sort_values(["num_sequences", "variant"], ascending=[False, True]).drop_duplicates(
            ["location", "date"], keep="first"
        )
        df = df[["location", "date", "num_sequences_total", "variant"]]
        df = df.assign(variant=df.variant.replace({"!non_who": "Others"}))
        df = df.rename(columns={"variant": "variant_dominant"})
        msk = df.num_sequences_total < 30
        df.loc[msk, "variant_dominant"] = pd.NA
        return df

    def pipe_variant_totals(self, df: pd.DataFrame) -> pd.DataFrame:
        # total = df.groupby(["location", "date", "num_sequences_total"])
        total = df[["location", "date", "num_sequences_total", "variant_dominant"]].drop_duplicates()
        total = total.rename(columns={"num_sequences_total": "num_sequences"})
        # Sort
        total = total.sort_values(["location", "date"])
        return total

    def pipe_per_capita(self, df: pd.DataFrame) -> pd.DataFrame:
        df_pop = pd.read_csv(PATHS.INTERNAL_INPUT_UN_POPULATION_FILE, index_col="entity")
        df = df.merge(df_pop["population"], left_on="location", right_index=True)
        df = df.assign(num_sequences_per_1M=(1000000 * df.num_sequences / df.population).round(2)).drop(
            columns=["population"]
        )
        return df

    def pipe_cumsum(self, df: pd.DataFrame) -> pd.DataFrame:
        df_cum = df.groupby(["location"])[["num_sequences", "num_sequences_per_1M"]].cumsum()
        df = df.assign(
            num_sequences_cumulative=df_cum.num_sequences,
            num_sequences_cumulative_per_1M=df_cum.num_sequences_per_1M.round(2),
        )
        return df

    def load(self, df: pd.DataFrame, output_path: str) -> None:
        # Export data
        if output_path.startswith("s3://"):
            obj_to_s3(df, s3_path=output_path, public=False)  # df, output_path, public=True)
        else:
            df.to_csv(output_path, index=False)

    def json_to_df(self, data: dict) -> pd.DataFrame:
        df = pd.json_normalize(data, record_path=["distribution"], meta=["country"]).melt(
            id_vars=["country", "total_sequences", "week"],
            var_name="cluster",
            value_name="num_sequences",
        )
        return df

    def pipe_filter_by_num_sequences(self, df: pd.DataFrame) -> pd.DataFrame:
        msk = df.total_sequences < self.num_sequences_total_threshold
        # Info
        _sk_perc_rows = round(100 * (msk.sum() / len(df)), 2)
        _sk_num_countries = df.loc[msk, "country"].nunique()
        _sk_countries_top = df[msk]["country"].value_counts().head(10).to_dict()
        print(
            f"Skipping {msk.sum()} datapoints ({_sk_perc_rows}%), affecting {_sk_num_countries} countries. Some are:"
            f" {_sk_countries_top}"
        )
        return df[~msk]

    def pipe_rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns=self.column_rename)

    def pipe_filter_variants(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter variants"""
        variants_ignore = [v["rename"] for _, v in self.variants_details.items() if v.get("ignore")]
        rows_init = df.shape[0]
        df = df[-df.variant.isin(variants_ignore)]
        rows_post = df.shape[0]
        ratio = round((rows_post - rows_init) / rows_init * 100, 2)
        print(f"Removed: variants {variants_ignore}. Went from {rows_init} to {rows_post} rows ({ratio}%).")
        return df

    def pipe_variants(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename variants"""
        # Modify/add columns
        df = df.assign(
            variant=df.cluster.str.replace("cluster_counts.", "", regex=True).replace(self.variants_mapping),
        ).drop(columns="cluster")
        return df

    def pipe_group_by_variants(self, df: pd.DataFrame) -> pd.DataFrame:
        cols_values = ["num_sequences"]
        cols_index = [c for c in df.columns if c not in cols_values]
        df = df.groupby(cols_index, as_index=False).sum()
        return df

    def pipe_check_variants(self, df: pd.DataFrame) -> pd.DataFrame:
        variants_missing = set(df.variant).difference(self.variants_mapping.values())
        if variants_missing:
            raise ValueError(f"Unknown variants {variants_missing}. Edit class attribute self.variants_details")
        return df

    def pipe_location(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.assign(
            location=df.country.replace(self.country_mapping),
        )
        return df.drop(columns=["country"])

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        dt = pd.to_datetime(df.week, format=DATE_FORMAT)
        dt = dt + timedelta(days=14)
        last_update = self._parse_last_update_date
        dt = dt.apply(lambda x: clean_date(min(x.date(), last_update), DATE_FORMAT))
        df = df.assign(
            date=dt,
        )
        return df.drop(columns=["week"])

    def pipe_filter_locations(self, df: pd.DataFrame) -> pd.DataFrame:
        # Filter locations
        dfc = pd.read_csv(PATHS.INTERNAL_INPUT_UN_POPULATION_FILE)
        df = df[df.location.isin(dfc.entity.unique())]
        return df

    def pipe_variant_others(self, df: pd.DataFrame) -> pd.DataFrame:
        df_a = df[["date", "location", "num_sequences_total"]].drop_duplicates()
        df_b = (
            df.groupby(["date", "location"], as_index=False)
            .agg({"num_sequences": sum})
            .rename(columns={"num_sequences": "all_seq"})
        )
        df_c = df_a.merge(df_b, on=["date", "location"])
        df_c = df_c.assign(others=df_c["num_sequences_total"] - df_c["all_seq"])
        df_c = df_c.melt(
            id_vars=["location", "date", "num_sequences_total"],
            value_vars="num_sequences_others",
            var_name="variant",
            value_name="num_sequences",
        )
        df = pd.concat([df, df_c])
        return df

    def pipe_variant_non_who(self, df: pd.DataFrame) -> pd.DataFrame:
        x = df[-df.variant.isin(self.variants_who)]
        if x.groupby(["location", "date"]).num_sequences_total.nunique().max() != 1:
            raise ValueError("Different value of `num_sequences_total` found for the same location and date")
        x = (
            x.groupby(["location", "date", "num_sequences_total"], as_index=False)
            .agg(
                {
                    "num_sequences": sum,
                }
            )
            .assign(variant="non_who")
        )
        df = pd.concat([df, x], ignore_index=True)
        return df

    def pipe_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.astype({"num_sequences_total": "Int64", "num_sequences": "Int64"})
        return df

    def pipe_percent(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(
            # perc_sequences=(100 * df["num_sequences"] / df["num_sequences_total"]).round(2),
            perc_sequences=((100 * df["num_sequences"] / df["num_sequences_total"]).round(2))
        )

    def pipe_correct_excess_percentage(self, df: pd.DataFrame) -> pd.DataFrame:
        # 1) `non_who`
        # Get excess
        x = df[df.variant.isin(self.variants_who + ["non_who"])]
        x = x.groupby(["location", "date"], as_index=False).agg({"perc_sequences": sum})
        x = x[abs(x["perc_sequences"] - 100) != 0]
        x["excess"] = x.perc_sequences - 100
        # Merge excess quantity with input df
        df = df.merge(x[["location", "date", "excess"]], on=["location", "date"], how="outer")
        df = df.assign(excess=df.excess.fillna(0))
        # Correct
        mask = df.variant.isin(["non_who"])
        df.loc[mask, "perc_sequences"] = (df.loc[mask, "perc_sequences"] - df.loc[mask, "excess"]).round(4)
        df = df.drop(columns="excess")
        # 2) `others`
        # Get excess
        x = df[-df.variant.isin(["non_who"])]
        x = x.groupby(["location", "date"], as_index=False).agg({"perc_sequences": sum})
        x = x[abs(x["perc_sequences"] - 100) != 0]
        x["excess"] = x.perc_sequences - 100
        # Merge excess quantity with input df
        df = df.merge(x[["location", "date", "excess"]], on=["location", "date"], how="outer")
        df = df.assign(excess=df.excess.fillna(0))
        # Correct
        mask = df.variant.isin(["others"])
        df.loc[mask, "perc_sequences"] = (df.loc[mask, "perc_sequences"] - df.loc[mask, "excess"]).round(4)
        df = df.drop(columns="excess")
        return df

    def pipe_omicron(self, df: pd.DataFrame) -> pd.DataFrame:
        # Get only Omicron rows
        msk = df.variant.str.startswith("Omicron")
        # Group
        dfg = df[msk].groupby(["location", "date"])
        # Sum values
        values = dfg[["num_sequences", "perc_sequences"]].sum()
        # Get num total
        num_seq_ttl = dfg["num_sequences_total"].unique()
        assert (num_seq_ttl.apply(len) == 1).all()
        num_seq_ttl = num_seq_ttl.apply(lambda x: x[0])
        # Build df
        values = values.merge(num_seq_ttl, left_index=True, right_index=True).reset_index().assign(variant="Omicron")
        df = pd.concat([df, values], ignore_index=True)
        return df

    def pipe_out(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[self.columns_out].sort_values(["location", "date", "variant"])  #  + ["perc_sequences_raw"]

    def run(self):
        data = self.extract()
        df = self.transform(data)
        self.load(df, PATHS.INTERNAL_OUTPUT_VARIANTS_FILE)
        # Sequencing
        df_seq = self.transform_seq(df)
        self.load(df_seq, PATHS.INTERNAL_OUTPUT_VARIANTS_SEQ_FILE)


def run_etl():
    etl = VariantsETL()
    etl.run()
