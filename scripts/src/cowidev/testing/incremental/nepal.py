import re
import tempfile

import pandas as pd
from pdfminer.high_level import extract_text

from cowidev.utils.web import request_json
from cowidev.utils.clean import clean_count, extract_clean_date
from cowidev.utils.utils import download_file_from_url
from cowidev.testing.utils.base import CountryTestBase


class Nepal(CountryTestBase):
    location: str = "Nepal"
    units: str = "samples tested"
    source_url: dict = {
        "api": "https://covid19.mohp.gov.np/covid/api/ministryrelease",
        "base": "https://covid19.mohp.gov.np/covid/englishSituationReport/",
    }
    source_url_ref: str = None
    source_label: str = "Ministry of Health and Population"
    regex: dict = {
        "date": r"(\d{1,2}\-\d{1,2}\-20\d{2})",
        "metrics": r"PCR \| Antigen (\d+) (\d+) PCR \| Antigen (\d+) (\d+)",
    }

    def read(self) -> pd.DataFrame:
        """Reads data from source."""
        links = request_json(self.source_url["api"])
        df = self._parse_data(links)
        return df

    def _parse_data(self, links: dict) -> pd.DataFrame:
        """Parses data from link."""
        # Obtain pdf url
        href = links["data"][0]["english_file"]
        self.source_url_ref = "{}{}".format(self.source_url["base"], href)
        # Extract text from pdf url
        text = self._extract_text_from_url()
        # Clean data
        df = self._parse_metrics(text)
        return df

    def _extract_text_from_url(self) -> str:
        """Extracts text from pdf."""
        with tempfile.NamedTemporaryFile() as tmp:
            download_file_from_url(self.source_url_ref, tmp.name)
            with open(tmp.name, "rb") as f:
                text = extract_text(f).replace("\n", " ")
        text = re.sub(r"\s+", " ", text)
        return text

    def _parse_metrics(self, text: str) -> pd.DataFrame:
        """Parses metrics from data."""
        # Extract data
        match_count = re.search(self.regex["metrics"], text)
        if not match_count:
            raise ValueError("Unable to extract data from text, please update the regex.")
        tests = clean_count(match_count.group(1)) + clean_count(match_count.group(2))
        positive = clean_count(match_count.group(3)) + clean_count(match_count.group(4))
        # Create dataframe
        df = {
            "Cumulative total": [tests],
            "positive": [positive],
        }
        return pd.DataFrame(df)

    def _parse_date(self, link: str) -> str:
        """Get date from link."""
        return extract_clean_date(link, self.regex["date"], "%d-%m-%Y")

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes date."""
        return df.assign(Date=self._parse_date(self.source_url_ref))

    def pipe_pr(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Positive Rate"""
        df = df.sort_values("Date")
        df = df.drop_duplicates(subset=["Date"], keep="first")
        df["Positive rate"] = (
            df["positive"].diff().rolling(7).sum().div(df["Cumulative total"].diff().rolling(7).sum()).round(3)
        ).fillna(0)
        return df

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data."""
        return df.pipe(self.pipe_date).pipe(self.pipe_metadata).pipe(self.pipe_merge_current).pipe(self.pipe_pr)

    def export(self):
        """Exports data to CSV."""
        df = self.read().pipe(self.pipeline)
        # Export to CSV
        self.export_datafile(df, extra_cols=["positive"], float_format="%.3f")


def main():
    Nepal().export()
