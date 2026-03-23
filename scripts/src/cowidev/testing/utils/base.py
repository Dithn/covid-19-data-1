import os

import pandas as pd

from cowidev import PATHS
from cowidev.utils.clean.numbers import metrics_to_num_int


COLUMNS_ORDER = [
    "Country",
    "Date",
    "Cumulative total",
    "Daily change in cumulative total",
    "Positive rate",
    "Units",
    "Source URL",
    "Source label",
    "Notes",
]


class CountryTestBase:
    location: str = None
    units: str = None
    source_url: str = None
    source_url_ref: str = None
    source_label: str = None
    notes: str = pd.NA
    rename_columns: dict = {}

    def __init__(self):
        if self.location == None:
            raise NotImplementedError("Please define class attribute `location`")
        # if self.units == None:
        #     raise NotImplementedError("Please define class attribute `units`")
        # if self.source_url_ref == None:
        #     raise NotImplementedError("Please define class attribute `source_url_ref`")
        # if self.source_label == None:
        #     raise NotImplementedError("Please define class attribute `source_label`")

    def get_output_path(self, filename=None):
        if filename is None:
            filename = self.location
        output_path = os.path.join(PATHS.INTERNAL_OUTPUT_TEST_MAIN_DIR, f"{filename}.csv")
        return output_path

    @property
    def output_path(self):
        return os.path.join(PATHS.INTERNAL_OUTPUT_TEST_MAIN_DIR, f"{self.location}.csv")

    def _postprocessing(self, df: pd.DataFrame, extra_cols: list):
        df = df.sort_values("Date")
        cols = [col for col in COLUMNS_ORDER if col in df.columns]
        if extra_cols:
            cols += extra_cols
        df = df[cols]
        return df

    def export_datafile(self, df, filename=None, attach=False, reset_index=False, extra_cols=None, **kwargs):
        output_path = self.get_output_path(filename)
        if attach:
            df = merge_with_current_data(df, output_path)
        df = metrics_to_num_int(df, ["Cumulative total", "Daily change in cumulative total"])
        df = self._postprocessing(df, extra_cols)
        if reset_index:
            df = df.reset_index(drop=True)
        df.to_csv(output_path, index=False, **kwargs)

    def load_datafile(self, filename=None):
        return pd.read_csv(self.get_output_path(filename))

    def _check_attributes(self, mapping):
        for field_raw, field in mapping.items():
            if field is None:
                raise ValueError(f"Please check class attribute {field_raw}, it can't be None!")

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        mapping = {
            "Country": self.location,
            "Units": self.units,
            "Notes": self.notes,
            "Source URL": self.source_url_ref,
            "Source label": self.source_label,
        }
        mapping = {k: v for k, v in mapping.items() if k not in df}
        self._check_attributes(mapping)
        return df.assign(**mapping)

    def pipe_rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns=self.rename_columns)

    def pipe_merge_current(self, df: pd.DataFrame):
        return merge_with_current_data(df, self.output_path)


def merge_with_current_data(df: pd.DataFrame, filepath: str) -> pd.DataFrame:
    df_current = pd.read_csv(filepath)
    df_current = df_current[df_current.Date < df.Date.min()]
    df = pd.concat([df_current, df]).sort_values("Date")
    # df = df.drop_duplicates(subset=[], keep='last')
    return df
