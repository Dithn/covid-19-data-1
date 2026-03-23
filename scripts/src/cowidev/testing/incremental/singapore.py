import pandas as pd
import re
from datetime import timedelta


from cowidev.testing import CountryTestBase
from cowidev.utils import clean_count, clean_date
from cowidev.utils.web.scraping import request_text


class Singapore(CountryTestBase):
    location = "Singapore"
    units = "samples tested"
    source_url = "https://www.moh.gov.sg/covid-19/statistics"
    source_label = "Ministry of Health Singapore"

    def read(self) -> pd.DataFrame:
        """Reads data from source."""
        data = self._parse_data()
        df = self._build_df(data)
        return df

    def _build_df(self, data: dict) -> pd.DataFrame:
        # Create dataframe
        df = pd.DataFrame([data])
        # Create date range (check week distance)
        dt_min = self._load_last_date() + timedelta(days=1)
        dt = clean_date(df.Date.max(), "%Y-%m-%d", as_datetime=True)
        if ((days_diff := (dt - dt_min).days) != 6) & (days_diff != -1):
            raise ValueError(f"Date distance is no longer a week ({days_diff})! Please check.")
        ds = pd.Series(pd.date_range(dt - timedelta(days=6), dt).astype(str), name="Date")
        # Distribute week value over 7 days
        df = df.merge(ds, how="right")
        df = df.assign(
            **{
                "Source URL": self.source_url,
                "Daily change in cumulative total": round(df["Daily change in cumulative total"].bfill()),
            }
        )
        return df

    def _read_art(self):
        text = request_text(self.source_url, mode="raw")
        table = pd.read_html(text, index_col=0)[5]
        art_count = clean_count(table.index[1].replace("~", ""))
        art_date = clean_date(
            re.search("Number of Reportable ART Swabs Tested \(as of (.*)\)", text).group(1), "%d %b %Y"
        )
        art = (art_date, art_count)
        return art

    def _read_pcr(self):
        text = request_text(self.source_url, mode="raw")
        table = pd.read_html(text, index_col=0)[9]
        pcr_count = clean_count(table.index[1].replace("~", ""))
        pcr_date = clean_date(re.search("Number of PCR Swabs Tested \(as of (.*)\)", text).group(1), "%d %b %Y")
        pcr = (pcr_date, pcr_count)
        return pcr

    def _parse_data(self) -> list:
        # Read both source data and merge
        art = self._read_art()
        pcr = self._read_pcr()

        if art[0] == pcr[0]:
            record = {
                "Date": art[0],
                "Daily change in cumulative total": art[1] + pcr[1],
            }
        else:
            raise Exception("ART and PCR dates do not match")

        return record

    def _load_last_date(self) -> str:
        """Loads the last date from the datafile."""
        df_current = self.load_datafile()
        date = df_current.Date.max()
        return clean_date(date, "%Y-%m-%d", as_datetime=True)

    def export(self):
        """Exports data to csv."""
        df = self.read().pipe(self.pipe_metadata)
        self.export_datafile(df, attach=True)


def main():
    Singapore().export()
