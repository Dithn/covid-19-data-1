import os
import pandas as pd
from typing import List

from cowidev import PATHS
from cowidev.utils.s3 import S3, obj_from_s3
from cowidev.utils.utils import make_monotonic as mkm
from cowidev.utils.clean.dates import localdate
from cowidev.utils.clean.numbers import metrics_to_num_int, metrics_to_num_float
from cowidev.vax.utils.files import export_metadata


COLUMNS_ORDER = [
    "location",
    "date",
    "vaccine",
    "source_url",
    "total_vaccinations",
    "people_vaccinated",
    "people_fully_vaccinated",
    "total_boosters",
]

COLUMNS_ORDER_AGE = [
    "location",
    "date",
    "age_group_min",
    "age_group_max",
    "people_vaccinated_per_hundred",
    "people_fully_vaccinated_per_hundred",
    "people_with_booster_per_hundred",
]

COLUMNS_ORDER_MANUF = [
    "location",
    "date",
    "vaccine",
    "total_vaccinations",
]

METRICS = [
    "total_vaccinations",
    "people_vaccinated",
    "people_fully_vaccinated",
    "total_boosters",
    "total_vaccinations_per_hundred",
    "people_vaccinated_per_hundred",
    "people_fully_vaccinated_per_hundred",
    "people_with_booster_per_hundred",
]


class CountryVaxBase:
    location: str = None

    def __init__(self):
        if self.location is None:
            raise NotImplementedError("Please define class attribute `location`")

    def from_ice(self):
        """Loads single CSV `location.csv` from S3 as DataFrame."""
        path = f"{PATHS.S3_VAX_ICE_DIR}/{self.location}.csv"
        _check_last_update(path, self.location)
        df = obj_from_s3(path)
        return df

    @property
    def output_path(self):
        """Country output file."""
        return os.path.join(PATHS.INTERNAL_OUTPUT_VAX_MAIN_DIR, f"{self.location}.csv")

    @property
    def output_path_age(self):
        """Country output file for age-group data."""
        return os.path.join(PATHS.INTERNAL_OUTPUT_VAX_AGE_DIR, f"{self.location}.csv")

    @property
    def output_path_manufacturer(self):
        """Country output file for manufacturer data."""
        return os.path.join(PATHS.INTERNAL_OUTPUT_VAX_MANUFACT_DIR, f"{self.location}.csv")

    def get_output_path(self, filename=None, age=False, manufacturer=False):
        if age:
            if filename is None:
                return self.output_path_age
            return os.path.join(PATHS.INTERNAL_OUTPUT_VAX_AGE_DIR, f"{filename}.csv")
        elif manufacturer:
            if filename is None:
                return self.output_path_manufacturer
            return os.path.join(PATHS.INTERNAL_OUTPUT_VAX_MANUFACT_DIR, f"{filename}.csv")
        else:
            if filename is None:
                return self.output_path
            return os.path.join(PATHS.INTERNAL_OUTPUT_VAX_MAIN_DIR, f"{filename}.csv")

    def load_datafile(self, **kwargs):
        return pd.read_csv(self.output_path, **kwargs)

    def last_update(self, **kwargs):
        df = self.load_datafile(**kwargs)
        return df.date.max()

    def make_monotonic(self, df, group_cols=None, max_removed_rows=10, strict=False):
        if group_cols:
            dfg = df.groupby(group_cols)
            dfg = list(dfg)
            dfs = []
            for df_vax in dfg:
                _df = mkm(
                    df=df_vax[1],
                    column_date="date",
                    column_metrics=[m for m in METRICS if m in df.columns],
                    max_removed_rows=max_removed_rows,
                    strict=strict,
                    new=True,
                )
                dfs.append(_df)
            return pd.concat(dfs, ignore_index=True)
        else:
            return mkm(
                df=df,
                column_date="date",
                column_metrics=[m for m in METRICS if m in df.columns],
                max_removed_rows=max_removed_rows,
                strict=strict,
                new=True,
            )

    def _postprocessing(self, df, valid_cols_only):
        """Minor post processing after all transformations.

        Basically sort by date, ensure correct column order, correct type for metrics.
        """
        df = metrics_to_num_int(df, METRICS)
        df = df.sort_values("date")
        cols = [col for col in COLUMNS_ORDER if col in df.columns]
        if not valid_cols_only:
            cols += [col for col in df.columns if col not in COLUMNS_ORDER]
        df = df[cols]
        df = df.drop_duplicates(subset=[m for m in METRICS if m in df.columns], keep="first")
        df = df.drop_duplicates(subset=["date"], keep="last")
        return df

    def _postprocessing_age(self, df):
        """Minor post processing after all transformations.

        Basically sort by date, ensure correct column order, correct type for metrics.
        """
        df = metrics_to_num_float(df, METRICS)
        df = df.sort_values(["date", "age_group_min", "age_group_max"])
        cols = [col for col in COLUMNS_ORDER_AGE if col in df.columns]
        df = df[cols]
        return df

    def _postprocessing_manufacturer(self, df):
        """Minor post processing after all transformations.

        Basically sort by date, ensure correct column order, correct type for metrics.
        """
        df = metrics_to_num_int(df, METRICS)
        df = df.sort_values(["vaccine", "date"])
        cols = [col for col in COLUMNS_ORDER_MANUF if col in df.columns]
        df = df[cols]

        df = df.drop_duplicates(subset=[m for m in METRICS + ["vaccine"] if m in df.columns], keep="first")
        df = df.drop_duplicates(subset=["date", "vaccine"], keep="last")
        return df

    def export_datafile(
        self,
        df=None,
        df_age=None,
        df_manufacturer=None,
        meta_age=None,
        meta_manufacturer=None,
        filename=None,
        attach=False,
        attach_age=False,
        attach_manufacturer=False,
        merge=False,
        reset_index=False,
        valid_cols_only=False,
        force_monotonic=False,
        **kwargs,
    ):
        """Export country data.

        Args:
            df (pd.DataFrame): Main country data.
            df_age (pd.DataFrame, optional): Country data by age group. Defaults to None.
            df_manufacturer (pd.DataFrame, optional): Country data by manufacturer. Defaults to None.
            meta_age (dict, optional): Country metadata by age. Defaults to None.
            meta_manufacturer (dict, optional): Country metadata by manufacturer. Defaults to None.
            filename (str, optional): Name of output file. If None, defaults to country name.
            attach (bool, optional): Set to True to attach to already existing data. Defaults to False.
            attach_age (bool, optional): Set to True to attach to already existing data. Defaults to False.
            attach_manufacturer (bool, optional): Set to True to attach to already existing data. Defaults to False.
            merge (bool): similar to attach but smarter.
            valid_cols_only (bool, optional): Export only valid columns. Defaults to False.
            reset_index (bool, optional): Brin index back as a column. Defaults to False.
            force_monotonic (bool, optional): Force timeseries to be monotonically increasing after exporting.
        """
        if df is not None:
            self._export_datafile_main(
                df,
                filename=filename,
                attach=attach,
                merge=merge,
                reset_index=reset_index,
                valid_cols_only=valid_cols_only,
                force_monotonic=force_monotonic,
                **kwargs,
            )
        if df_age is not None:
            self._export_datafile_age(df_age, meta_age, filename=filename, attach=attach_age)
        if df_manufacturer is not None:
            self._export_datafile_manufacturer(
                df_manufacturer, meta_manufacturer, filename=filename, attach=attach_manufacturer
            )

    def pipe_merge_with_current(self, df, filename=None):
        filename = self.get_output_path(filename)
        df = merge_with_current_data(df, filename)
        return df

    def _export_datafile_main(
        self,
        df,
        filename,
        attach=False,
        merge=False,
        reset_index=False,
        valid_cols_only=False,
        force_monotonic=False,
        **kwargs,
    ):
        """Export main data."""
        filename = self.get_output_path(filename)
        if merge:
            df = merge_with_current_data(df, filename, smart=True)
        elif attach:
            df = merge_with_current_data(df, filename)
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"df must be a pandas DataFrame!. Isntead {type(df).__name__} was detected.")
        if "Cayman" in filename:
            print(filename, df.shape)
        df = self._postprocessing(df, valid_cols_only)
        if reset_index:
            df = df.reset_index(drop=True)
        df.to_csv(filename, index=False, **kwargs)
        if force_monotonic:
            self.force_monotonic(filename)

    def _export_datafile_age(self, df, metadata, filename, attach):
        """Export age data."""
        filename = self.get_output_path(filename, age=True)
        if attach:
            df = merge_with_current_data(df, filename)
        df = self._postprocessing_age(df)
        self._export_datafile_secondary(df, metadata, filename, PATHS.INTERNAL_OUTPUT_VAX_META_AGE_FILE)

    def _export_datafile_manufacturer(self, df, metadata, filename, attach):
        """Export manufacturer data"""
        filename = self.get_output_path(filename, manufacturer=True)
        if attach:
            df = merge_with_current_data(df, filename)
        df = self._postprocessing_manufacturer(df)
        self._export_datafile_secondary(df, metadata, filename, PATHS.INTERNAL_OUTPUT_VAX_META_MANUFACT_FILE)

    def _export_datafile_secondary(self, df, metadata, output_path, output_path_meta):
        """Export secondary data."""
        # Check metadata
        self._check_metadata(metadata)
        # Export data
        df.to_csv(output_path, index=False)
        # Export metadata
        export_metadata(df, metadata["source_name"], metadata["source_url"], output_path_meta)

    def _check_metadata(self, metadata):
        if not isinstance(metadata, dict):
            raise ValueError("The `metadata` object must be a dictionary!")
        if ("source_name" not in metadata) or ("source_url" not in metadata):
            raise ValueError("`metadata` must contain keys 'source_name' and 'source_url'")
        if not (isinstance(metadata["source_name"], str) and isinstance(metadata["source_url"], str)):
            raise ValueError("metadata['source_name'] and metadata['source_url'] must be strings!")

    def _check_attributes(self, mapping):
        for field_raw, field in mapping.items():
            if field is None:
                raise ValueError(f"Please check class attribute {field_raw}, it can't be None!")

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        if is_series := isinstance(df, pd.Series):
            df = pd.DataFrame(df).T
        mapping = {
            "location": self.location,
            "source_url": self.source_url_ref,
        }
        mapping = {k: v for k, v in mapping.items() if k not in df}
        self._check_attributes(mapping)
        df = df.assign(**mapping)
        if is_series:
            return df.iloc[0]
        else:
            return df

    def pipe_rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns=self.rename_columns)

    def force_monotonic(self, filename: str = None, **kwargs):
        if filename is None:
            filename = self.output_path
        df = pd.read_csv(filename)
        df = df.pipe(self.make_monotonic, **kwargs)
        self.export_datafile(df, filename=filename.replace(".csv", ""))

    def pipe_age_per_capita(self, df: pd.DataFrame) -> pd.DataFrame:
        # Build population df by age group
        pop_age = _build_population_age_group_df(self.location, df)
        # Normalize
        df = df.merge(pop_age, on=["age_group_min", "age_group_max"])
        metrics = ["people_vaccinated", "people_fully_vaccinated", "people_with_booster"]
        for metric in metrics:
            df = df.assign(**{f"{metric}_per_hundred": (df[metric] / df.population * 100).round(2)})
        return df

    def pipe_check_vaccine(self, df: pd.DataFrame, vaccines_accepted=None) -> pd.DataFrame:
        if vaccines_accepted is None:
            vaccines_accepted = self.vaccine_mapping.keys()
        self.check_column_values(df, "vaccine", vaccines_accepted)
        return df

    def check_column_values(self, df: pd.DataFrame, col_name: str, values_accepted: list) -> pd.DataFrame:
        values = set(df[col_name])
        unknown_vaccines = set(values).difference(values_accepted)
        if unknown_vaccines:
            raise ValueError(f"Found unknown values for `{col_name}`: {unknown_vaccines}")

    def pipe_filter_dp(self, df: pd.DataFrame, dates: List[str], metrics: List[str] = None) -> pd.DataFrame:
        if metrics is None:
            df = df[-df.date.isin(dates)]
        else:
            df.loc[df.date.isin(dates), metrics] = None
        return df

    def pipe_filer_dp_age(df, ages, dates, column_date="date", column_age="age_group"):
        assert len(ages) == len(dates), "Length of `ages` and `dates` should be the same!"
        msk = sum(((df[column_date] == date) & (df[column_age] == age)) for date, age in zip(dates, ages)).astype(bool)
        return df[~msk]

    def load_archived_data(self, filename: str = None, **kwargs) -> pd.DataFrame:
        if filename is None:
            filename = f"{self.location}.csv"
        filename = os.path.join(PATHS.INTERNAL_OUTPUT_VAX_MAIN_DIR, "archived", filename)
        return pd.read_csv(filename, **kwargs)

def _build_population_age_group_df(location, df):
    # Read raw population by age
    pop_age = pd.read_csv(PATHS.INTERNAL_INPUT_UN_POPULATION_AGE_FILE, index_col="location")
    # Filter location
    pop_age = pop_age.loc[location]
    # Extract age groups of interest
    ages = df[["age_group_min", "age_group_max"]].drop_duplicates()
    # ages = df[["age_group_min", "age_group_max"]].drop_duplicates().replace("", 1000).astype(float).values.tolist()
    ages["age_group_max"] = ages["age_group_max"].replace("", 1000).astype(float).fillna(1000)
    ages["age_group_min"] = ages["age_group_min"].replace("", -1000).astype(float).fillna(-1000)
    ages = ages.values.tolist()
    # # Build population dataframe for age groups
    records = []
    for age_min, age_max in ages:
        msk = (pop_age.age >= age_min) & (pop_age.age <= age_max)
        records.append(
            {
                "age_group_min": age_min,
                "age_group_max": age_max,
                "population": pop_age.loc[msk, "population"].sum(),
            }
        )
    # Build Dataframe
    pop_age = pd.DataFrame(records)
    # return pop_age
    pop_age = pop_age.astype(int).astype({"age_group_min": str, "age_group_max": str})
    pop_age = pop_age.assign(
        age_group_max=pop_age.age_group_max.replace("1000", ""),
        age_group_min=pop_age.age_group_min.replace("-1000", ""),
    )
    return pop_age


def _check_last_update(path, country):
    metadata = S3().get_metadata(path)
    last_update = metadata["LastModified"]
    now = localdate(force_today=True, as_datetime=True)
    num_days = (now - last_update).days
    if num_days > 4:  # Allow maximum 4 days delay
        raise FileExistsError(
            f"ICE File for {country} is too old ({num_days} days old)! Please check cowidev.vax.icer"
        )


def merge_with_current_data(df: pd.DataFrame, filepath: str, smart: bool = False) -> pd.DataFrame:
    if os.path.isfile(filepath):
        # Load
        df_current = pd.read_csv(filepath)
        # Type check
        if isinstance(df, pd.Series):
            df = df.to_frame().T
        elif not isinstance(df, pd.DataFrame):
            raise TypeError(f"`df` must be a pandas DataFrame!. Instead {type(df).__name__} was detected.")

        # Merge: keep all fields from current data and complement with new ones. Using pandas.merge
        if smart:
            cols_ex = ["date", "location"]
            df_current.columns = [f"{col}_current" if col not in cols_ex else col for col in df_current.columns]
            df.columns = [f"{col}_new" if col not in cols_ex else col for col in df.columns]
            df = df_current.merge(df, on=["date", "location"], how="outer")
            print(df.columns)
            if "total_vaccinations_new" not in df.columns:
                df["total_vaccinations_new"] = pd.NA
            if "people_vaccinated_new" not in df.columns:
                df["people_vaccinated_new"] = pd.NA
            if "people_fully_vaccinated_new" not in df.columns:
                df["people_fully_vaccinated_new"] = pd.NA
            if "total_boosters_new" not in df.columns:
                df["total_boosters_new"] = pd.NA
            df = df.assign(
                total_vaccinations=df["total_vaccinations_new"].fillna(df["total_vaccinations_current"]),
                people_vaccinated=df["people_vaccinated_new"].fillna(df["people_vaccinated_current"]),
                people_fully_vaccinated=df["people_fully_vaccinated_new"].fillna(
                    df["people_fully_vaccinated_current"]
                ),
                total_boosters=df["total_boosters_new"].fillna(df["total_boosters_current"]),
                vaccine=df["vaccine_new"].fillna(df["vaccine_current"]),
                source_url=df["source_url_new"].fillna(df["source_url_current"]),
            )
            df = df[COLUMNS_ORDER]
        # Attach: Preserve current data up to date from new data. Using pandas.concat.
        else:
            # remove dates un current that are also present in df (they will be replaced)
            df_current = df_current[~df_current.date.isin(df.date)]
            df = pd.concat([df, df_current])
        df = df.sort_values(by="date")
    return df
