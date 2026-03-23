from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

import pandas as pd

from cowidev.utils.s3 import obj_from_s3


@dataclass
class Grapheriser:
    location: str = "location"
    date: str = "date"
    date_ref: datetime = datetime(2020, 1, 21)
    fillna: bool = False
    fillna_0: bool = True
    pivot_column: str = None
    pivot_values: str = None
    suffixes: list = None
    function_input: Callable = lambda x: x
    function_output: Callable = lambda x: x
    columns_non_fillna_0: list = field(default_factory=lambda: [])

    @property
    def columns_metadata(self) -> list:
        return ["Country", "Year"]

    @property
    def metric2suffix(self) -> dict:
        if len(self.pivot_values_list) == len(self.suffixes_list):
            return dict(zip(self.pivot_values_list, self.suffixes_list))
        else:
            raise ValueError(f"`suffixes` and `pivot_values` should be lists of the same length")

    @property
    def pivot_values_list(self) -> list:
        if not isinstance(self.pivot_values, list):
            return [self.pivot_values]
        return self.pivot_values

    @property
    def suffixes_list(self) -> list:
        suffizes = self.suffixes
        if not isinstance(self.suffixes, list):
            suffizes = [self.suffixes]
        return ["" if s is None else s for s in suffizes]

    @property
    def do_pivot(self):
        return self.pivot_column is not None and self.pivot_values is not None

    def columns_data(self, df: pd.DataFrame) -> list:
        return [col for col in df.columns if col not in self.columns_metadata]

    def pipe_pivot(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pivot values of columns of interest."""
        if self.do_pivot:
            return df.pivot(
                index=[self.location, self.date],
                columns=self.pivot_column,
                values=self.pivot_values_list,
            ).reset_index()
        return df

    def pipe_metadata_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename columns and convert date to Year grapher metric."""
        df = (
            df.rename(
                columns={
                    self.location: "Country",
                }
            )
            .assign(date=(df[self.date] - self.date_ref).dt.days)
            .rename(columns={"date": "Year"})
        ).copy()
        return df

    def pipe_normalize_columns(self, df):
        """Normalize column names.

        If columns are multiindex (of length 2), use first and second positions to create new column name.

        This only applies if pivot has been done, i.e. `pivot_column` and `pivot_values` are not None.
        """

        def _normalize_column(column):
            if len(column) != 2:
                raise ValueError("Column is expected to have length 2")
            if column[1]:
                column_new = f"{column[1]}{self.metric2suffix.get(column[0], '')}"
            else:
                column_new = column[0]
            return column_new

        if self.do_pivot:
            df.columns = [_normalize_column(xx) for xx in df.columns]
        return df

    def pipe_order_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Re-order the columns of the dataframe.

        First columns are [Country, Year]
        """
        col_order = self.columns_metadata + self.columns_data(df)
        df = df[col_order].sort_values(col_order)
        return df

    def pipe_fillna(self, df: pd.DataFrame) -> pd.DataFrame:
        columns_data = self.columns_data(df)
        if self.fillna:
            df[columns_data] = df.groupby(["Country"])[columns_data].fillna(method="ffill")
        if self.fillna_0:
            cols_fillna0 = [c for c in columns_data if c not in self.columns_non_fillna_0]
            df[cols_fillna0] = df[cols_fillna0].fillna(0)
        return df

    def read(self, input_path: str):
        if input_path.startswith("s3://"):
            return obj_from_s3(input_path, parse_dates=[self.date])
        return pd.read_csv(input_path, parse_dates=[self.date])

    def pipeline(self, df: pd.DataFrame):
        df = (
            df.pipe(self.function_input)
            .pipe(self.pipe_pivot)
            .pipe(self.pipe_metadata_columns)
            .pipe(self.pipe_normalize_columns)
            .pipe(self.pipe_order_columns)
            .pipe(self.pipe_fillna)
            .pipe(self.function_output)
        )
        return df

    def run(self, input_path: str, output_path: str):
        df = self.read(input_path)
        df = df.pipe(self.pipeline)
        df.to_csv(output_path, index=False)
