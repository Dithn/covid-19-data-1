import json
import requests

import pandas as pd

from cowidev.utils import clean_count, clean_date
from cowidev.vax.utils.base import CountryVaxBase


class SouthAfrica(CountryVaxBase):
    location: str = "South Africa"
    source_url: str = "https://wabi-west-europe-api.analysis.windows.net/public/reports/querydata?synchronous=true"
    source_url_ref: str = "https://sacoronavirus.co.za/latest-vaccine-statistics/"
    payload_vars = {
        "Pfizer_first": {
            "Value": "'Pfizer'",
            "Entity": "Vaccinations Administered Measures",
            "Property": "First Dose Total",
            "Name": "Vaccinations Administered Measures.First Dose Total",
        },
        "Johnson_first": {
            "Value": "'Johnson & Johnson'",
            "Entity": "Vaccinations Administered Measures",
            "Property": "First Dose Total",
            "Name": "Vaccinations Administered Measures.First Dose Total",
        },
        "Pfizer_second": {
            "Value": "'Pfizer'",
            "Entity": "Vaccinations Administered Measures",
            "Property": "Second Dose Total",
            "Name": "Vaccinations Administered Measures.Second Dose Total",
        },
        "Johnson_booster": {
            "Value": "'Johnson & Johnson'",
            "Entity": "Boosters Measures",
            "Property": "Booster Totals",
            "Name": "Boosters Measures.Booster Totals",
        },
        "Pfizer_booster": {
            "Value": "'Pfizer'",
            "Entity": "Boosters Measures",
            "Property": "Booster Totals",
            "Name": "Boosters Measures.Booster Totals",
        },
    }

    @property
    def headers(Self):
        """Headers for the request"""
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:85.0) Gecko/20100101 Firefox/85.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US",
            "X-PowerBI-ResourceKey": "03e532ee-b92a-44a5-9be9-d28054e54995",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://app.powerbi.com",
            "Referer": "https://app.powerbi.com/",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }

    def _payload(self, payload_var: str = "Pfizer_first") -> dict:
        """
        Request payload for the source.

            Parameters:
                        payload_var (str): A key in payload_vars (e.g. "Pfizer_first")
            Returns:
                        dict: A payload for the request
        """
        payload = {
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
                                            {
                                                "Name": "v",
                                                "Entity": "Vaccinations Administered Measures",
                                                "Type": 0,
                                            },
                                            {
                                                "Name": "v1",
                                                "Entity": "Vaccine Manufacturer",
                                                "Type": 0,
                                            },
                                        ],
                                        "Select": [
                                            {
                                                "Measure": {
                                                    "Expression": {"SourceRef": {"Source": "v"}},
                                                    "Property": "First Dose Total",
                                                },
                                                "Name": "Vaccinations Administered Measures.First Dose Total",
                                            }
                                        ],
                                        "Where": [
                                            {
                                                "Condition": {
                                                    "In": {
                                                        "Expressions": [
                                                            {
                                                                "Column": {
                                                                    "Expression": {"SourceRef": {"Source": "v1"}},
                                                                    "Property": "Vaccine Manufacturer",
                                                                }
                                                            }
                                                        ],
                                                        "Values": [[{"Literal": {"Value": "'Pfizer'"}}]],
                                                    }
                                                }
                                            }
                                        ],
                                    },
                                    "ExecutionMetricsKind": 1,
                                }
                            }
                        ]
                    },
                    "QueryId": "",
                    "ApplicationContext": {
                        "DatasetId": "6f42ba54-a8f6-46a6-afab-bedcd3dd1563",
                    },
                }
            ],
            "cancelQueries": [],
            "modelId": 4449930,
        }
        payload["queries"][0]["Query"]["Commands"][0]["SemanticQueryDataShapeCommand"]["Query"]["From"][0][
            "Entity"
        ] = self.payload_vars[payload_var]["Entity"]
        payload["queries"][0]["Query"]["Commands"][0]["SemanticQueryDataShapeCommand"]["Query"]["Select"][0][
            "Measure"
        ]["Property"] = self.payload_vars[payload_var]["Property"]
        payload["queries"][0]["Query"]["Commands"][0]["SemanticQueryDataShapeCommand"]["Query"]["Select"][0][
            "Name"
        ] = self.payload_vars[payload_var]["Name"]
        payload["queries"][0]["Query"]["Commands"][0]["SemanticQueryDataShapeCommand"]["Query"]["Where"][0][
            "Condition"
        ]["In"]["Values"][0][0]["Literal"]["Value"] = self.payload_vars[payload_var]["Value"]
        return payload

    def read(self) -> tuple:
        """Reads the data from the source"""
        df_main, df_manufacturer = self._parse_data()
        return df_main, df_manufacturer

    def _parse_data(self) -> tuple:
        """Parses the data from the source."""
        # Pfizer first dose
        response = json.loads(
            requests.post(
                self.source_url, headers=self.headers, data=json.dumps(self._payload("Pfizer_first"))
            ).content
        )
        Pfizer_first = response["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0]["DM0"][0]["M0"]
        date = response["results"][0]["result"]["data"]["timestamp"]
        # Pfizer second dose
        response = json.loads(
            requests.post(
                self.source_url, headers=self.headers, data=json.dumps(self._payload("Pfizer_second"))
            ).content
        )
        Pfizer_second = response["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0]["DM0"][0]["M0"]
        # Pfizer booster
        response = json.loads(
            requests.post(
                self.source_url, headers=self.headers, data=json.dumps(self._payload("Pfizer_booster"))
            ).content
        )
        Pfizer_booster = response["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0]["DM0"][0]["M0"]
        # Johnson first dose
        response = json.loads(
            requests.post(
                self.source_url, headers=self.headers, data=json.dumps(self._payload("Johnson_first"))
            ).content
        )
        Johnson_first = response["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0]["DM0"][0]["M0"]
        # Johnson booster
        response = json.loads(
            requests.post(
                self.source_url, headers=self.headers, data=json.dumps(self._payload("Johnson_booster"))
            ).content
        )
        Johnson_booster = response["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0]["DM0"][0]["M0"]
        # parse date
        date = self._parse_date(date)
        # create metrics list
        metrics = [
            clean_count(Pfizer_first),
            clean_count(Pfizer_second),
            clean_count(Pfizer_booster),
            clean_count(Johnson_first),
            clean_count(Johnson_booster),
        ]
        # build dataframe
        df_main, df_manufacturer = self._build_df(metrics, date)
        return df_main, df_manufacturer

    def _parse_date(self, date: str) -> str:
        """Parses the date from the list."""
        return clean_date(date, "%Y-%m-%dT%H:%M:%S.%fZ")

    def _build_df(self, metrics: list, date: str) -> tuple:
        """Builds DataFrame from metrics."""
        # Create main variables
        total_vaccinations = sum(metrics)
        people_vaccinated = metrics[0] + metrics[3]
        people_fully_vaccinated = metrics[1] + metrics[3]
        total_boosters = metrics[2] + metrics[4]
        # Create manufacturer variables
        pfizer = metrics[0] + metrics[1] + metrics[2]
        jandj = metrics[3] + metrics[4]
        # Create main dataseries
        df_main = {
            "date": [date],
            "total_vaccinations": [total_vaccinations],
            "people_vaccinated": [people_vaccinated],
            "people_fully_vaccinated": [people_fully_vaccinated],
            "total_boosters": [total_boosters],
        }
        # Create manufacturer dataframe
        df_manufacturer = {
            "date": [date, date],
            "total_vaccinations": [jandj, pfizer],
        }
        return pd.DataFrame(df_main), pd.DataFrame(df_manufacturer)

    def pipe_manufacturer_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes vaccine names for manufacturer data."""
        return df.assign(**{"vaccine": ["Johnson&Johnson", "Pfizer/BioNTech"]})

    def pipe_manufacturer_location(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes location for manufacturer data."""
        return df.assign(location=self.location)

    def pipeline_manufacturer(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for manufacturer data."""
        return df.pipe(self.pipe_manufacturer_vaccine).pipe(self.pipe_manufacturer_location)

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes vaccine names for main data."""
        return df.assign(vaccine="Johnson&Johnson, Pfizer/BioNTech")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for main data."""
        return df.pipe(self.pipe_metadata).pipe(self.pipe_vaccine)

    def export(self):
        """Exports data to CSV."""
        df_main, df_manufacturer = self.read()
        # Pipelines
        df_main = df_main.pipe(self.pipeline)
        df_manufacturer = df_manufacturer.pipe(self.pipeline_manufacturer)
        # Export to CSV
        self.export_datafile(
            df=df_main,
            df_manufacturer=df_manufacturer,
            attach=True,
            attach_manufacturer=True,
            meta_manufacturer={
                "source_name": "National Department of Health",
                "source_url": self.source_url_ref,
            },
        )


def main():
    SouthAfrica().export()
