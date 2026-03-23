import json
import requests

import pandas as pd

from cowidev.utils import clean_count
from cowidev.utils.clean.dates import localdate, clean_date
from cowidev.testing.utils.base import CountryTestBase


class Jordan(CountryTestBase):
    location: str = "Jordan"
    units: str = "tests performed"
    source_label: str = "Ministry of Health"
    week: str = localdate("Asia/Amman", as_datetime=True).isocalendar().week
    notes: str = ""
    source_url: str = (
        "https://wabi-west-europe-d-primary-api.analysis.windows.net/public/reports/querydata?synchronous=true"
    )
    source_url_ref: str = "https://corona.moh.gov.jo/ar"

    def read(self) -> pd.DataFrame:
        """Reads the data from the source"""
        try:
            count = self._request()
            return self._df_builder(count)
        except KeyError:
            raise KeyError("No value found. Please modify the payload and headers.")

    @property
    def headers(Self):
        """Headers for the request"""
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:85.0) Gecko/20100101 Firefox/85.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US",
            "X-PowerBI-ResourceKey": "f29483dd-2cd3-4be1-9fbd-6c67f0ca1037",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://app.powerbi.com",
            "Referer": "https://app.powerbi.com/",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }

    def payload(self, week: str = None) -> dict:
        """Request payload"""
        data = {
            "version": "1.0.0",
            "queries": [
                {
                    "Query": {
                        "Commands": [
                            {
                                "SemanticQueryDataShapeCommand": {
                                    "Query": {
                                        "Version": 2,
                                        "From": [
                                            {"Name": "w", "Entity": "weekly data", "Type": 0},
                                        ],
                                        "Select": [
                                            {
                                                "Aggregation": {
                                                    "Expression": {
                                                        "Column": {
                                                            "Expression": {"SourceRef": {"Source": "w"}},
                                                            "Property": "مجموع الفحوصات المخبرية التراكمي",
                                                        }
                                                    },
                                                    "Function": 0,
                                                },
                                                "Name": "Sum(weekly data.مجموع الفحوصات المخبرية التراكمي)",
                                            }
                                        ],
                                        "Where": [
                                            {
                                                "Condition": {
                                                    "In": {
                                                        "Expressions": [
                                                            {
                                                                "Column": {
                                                                    "Expression": {"SourceRef": {"Source": "w"}},
                                                                    "Property": "week",
                                                                }
                                                            }
                                                        ],
                                                        "Values": [[{"Literal": {"Value": f"{week}L"}}]],
                                                    }
                                                }
                                            },
                                        ],
                                    },
                                    "ExecutionMetricsKind": 1,
                                }
                            }
                        ]
                    },
                    "QueryId": "",
                    "ApplicationContext": {
                        "DatasetId": "805d8b47-2e08-46cc-b1cd-7937fe585c59",
                    },
                }
            ],
            "cancelQueries": [],
            "modelId": 1187812,
        }
        return data

    def _request(self) -> dict:
        """Requests data from source."""
        response = json.loads(
            requests.post(self.source_url, headers=self.headers, data=json.dumps(self.payload(str(self.week)))).content
        )["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0]["DM0"][0]
        if "M0" in response.keys():
            response = response["M0"]
        else:
            self.week -= 1
            response = self._request()
        return response

    def _week_to_date(self, week: int) -> str:
        """Converts week to date."""
        year = localdate("Asia/Amman", as_datetime=True).isocalendar().year
        date = clean_date(f"{year} {week} +5", "%Y %W +%w")
        return date

    def _df_builder(self, count: str) -> pd.DataFrame:
        """Builds dataframe from the text data"""
        df = pd.DataFrame({"Cumulative total": [clean_count(count)]})
        return df

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes date."""
        return df.assign(Date=self._week_to_date(self.week))

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data."""
        return df.pipe(self.pipe_date).pipe(self.pipe_metadata)

    def export(self):
        """Exports data to CSV."""
        df = self.read().pipe(self.pipeline)
        # Export to CSV
        self.export_datafile(df, attach=True)


def main():
    Jordan().export()
