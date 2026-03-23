import re
import os
import tempfile

import requests
from pdfminer.high_level import extract_text
import pandas as pd

from cowidev.utils import clean_date_series
from cowidev.utils.clean.dates import localdatenow
from cowidev.utils.gdrive import download_folder, download_file, list_files
from cowidev.testing import CountryTestBase


class Philippines(CountryTestBase):
    location = "Philippines"
    source_label = "Philippines Department of Health"
    units = "people tested"
    _base_url = "https://drive.google.com/drive/folders/1ZPPcVU4M7T-dtRyUceb0pMAd8ickYf8o"
    rename_columns = {
        "report_date": "Date",
        "cumulative_unique_individuals": "Cumulative total",
    }

    def read(self):
        id_ = self._get_file_id()
        with tempfile.NamedTemporaryFile() as tmp:
            url = f"https://drive.google.com/uc?id={id_}"
            download_file(url, output=tmp.name, quiet=True)
            df = pd.read_csv(tmp.name, usecols=["report_date", "cumulative_unique_individuals"])
            self.source_url_ref = "https://drive.google.com/drive/folders/1mqpDYkXll3GPM4bFjMstuwPjQPKozoTv"  # url
            return df

    def _get_file_id(self):
        id_ = self._get_id_folder()
        files = list_files(id_)
        for f in files:
            if re.search(r"Testing Aggregates\.csv", f["title"]):
                return f["id"]

    def _get_id_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Download file
            download_folder(self._base_url, output=tmp)
            # Get downloaded relevant file path
            f = [f for f in os.listdir(tmp) if "READ ME FIRST" in f][0]
            pdf_path = os.path.join(tmp, f)
            # Get id of relevant folder
            return self._parse_drive_id_from_pdf(pdf_path)

    def _parse_drive_id_from_pdf(self, pdf_path):
        # Get link from pdf
        with open(pdf_path, "rb") as f:
            text = extract_text(f)
        link = re.search(r"https://bit\.ly/.*", text).group()
        # Unshorten
        resp = requests.get(link)
        link = resp.url
        # Get id
        return link.split("/")[-1].split("?")[-2]

    def pipe_date(self, df: pd.DataFrame):
        return df.assign(Date=clean_date_series(df.Date, "%d/%m/%Y"))

    def pipe_aggregate(self, df: pd.DataFrame):
        return df.groupby("Date", as_index=False).sum()

    def pipe_checks(self, df: pd.DataFrame):
        n = 20
        if df.Date.isna().any():
            raise ValueError("Some `Date` have NaN values!")
        if not (df.Date.max() > localdatenow(minus_days=n)):
            raise ValueError(f"Data has not been updated for more than {n} days! Check source.")
        return df

    def pipeline(self, df: pd.DataFrame):
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_date)
            .pipe(self.pipe_aggregate)
            .pipe(self.pipe_checks)
            .pipe(self.pipe_metadata)
        )

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Philippines().export()
