from distutils.command.clean import clean
import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.utils import clean_date_series, clean_count


class SouthKorea(CountryTestBase):
    location = "South Korea"
    units = "people tested"
    source_url_ref = "https://sites.google.com/view/snuaric/data-service/covid-19/covid-19-data"
    source_label = "Korea Disease Control and prevention Agency"
    notes = "Data made available by Asia Regional Information Center at Seoul National University"

    def _read_old(self):
        ## data < 2020-12-18; 'Number of suspicious report testing' (의심신고 검사자 수)
        df = pd.read_csv(
            "https://docs.google.com/spreadsheets/d/10c9jNi8VnV0YYCfV_7AZrzBY5l18dOFHEJMIJsP4THI/export?format=csv&gid=334130338",
            usecols=["DATE", "TOTAL_TEST"],
        )
        # Daily change and clean
        df = df[pd.to_numeric(df["TOTAL_TEST"], errors="coerce").notnull()]
        df = df.assign(Date=clean_date_series(df["DATE"], "%Y-%m-%d"))
        df["Daily change in cumulative total"] = df["TOTAL_TEST"].astype("int32").diff(periods=-1)
        df["TOTAL_TEST"] = df["TOTAL_TEST"].apply(clean_count)
        return df[["Date", "Daily change in cumulative total"]].loc[df["Date"] < "2020-12-18"]

    def _read_new(self):
        df = pd.read_csv(
            "https://docs.google.com/spreadsheets/d/10c9jNi8VnV0YYCfV_7AZrzBY5l18dOFHEJMIJsP4THI/export?format=csv&gid=512078862",
            usecols=[
                "Date",
                "Total",
                "선별진료소(통합)",
                "의심신고 검사자 수",
                "임시선별검사소 검사건수",
                "수도권 임시선별검사소 검사건수",
                "비수도권 임시선별검사소",
            ],
        )
        df = df.assign(Date=clean_date_series(df["Date"], "%Y-%m-%d"))
        # 2021-04-21 < data < 2021-10-25; 'Number of testing at temporary screening stations' (임시선별검사소 검사건수) = 'Number of inspections by temporary screening and inspection centers in the metropolitan area'
        # (수도권 임시선별검사소 검사건수) + 'Non-Metropolitan Temporary Screening Center' (비수도권 임시선별검사소)
        df.iloc[:, 4].fillna((df.iloc[:, 5] + df.iloc[:, 6]), inplace=True)

        ## 2020-12-17 < data < 2022-02-08; 'Number of testing at screening stations' (Aggregate) (선별진료소(통합)) = 'Number of suspicious report testing' (의심신고 검사자 수) + 'Number of testing at temporary screening stations' (임시선별검사소 검사건수)
        df.iloc[:, 2].fillna((df.iloc[:, 3] + df.iloc[:, 4]), inplace=True)

        ## Use 'total' after 2022-02-06
        df.loc[df["Date"] > "2022-02-06", "선별진료소(통합)"] = df["Total"]

        df["Daily change in cumulative total"] = df["선별진료소(통합)"]
        df["Daily change in cumulative total"] = pd.to_numeric(
            df["Daily change in cumulative total"].str.replace(",", "")
        )
        return df[["Date", "Daily change in cumulative total"]]

    def read(self):
        old = self._read_old()
        new = self._read_new()
        df = pd.concat([new, old], ignore_index=True).dropna()
        return df

    def pipeline(self, df: pd.DataFrame):
        df = df.pipe(self.pipe_metadata)
        return df

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, reset_index=True)


def main():
    SouthKorea().export()
