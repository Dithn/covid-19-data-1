import json

import pandas as pd

from cowidev.utils.gdrive import GSheetApi


class TestingGSheet:
    def __init__(self, credentials_file, sheet_id: str):
        self._api = GSheetApi(credentials_file)
        self.sheet_id = sheet_id
        self.sheets = self._api.sheets
        self.sheet = self._api.get_sheet(self.sheet_id)
        # self.metadata = self.get_metadata()
        print(2)

    @classmethod
    def from_json(cls, path: str):
        """Load sheet from config file."""
        with open(path, "rb") as f:
            conf = json.load(f)
        return cls(
            credentials_file=conf["google_credentials"],
            sheet_id=conf["google_spreadsheet_testing_id"],
        )

    def get_metadata(self, refresh: bool = False) -> pd.DataFrame:
        """Get metadata from LOCATIONS tab."""
        if refresh:
            self.sheet = self._api.get_sheet(self.sheet_id)
        metadata = self.sheet.first_sheet.to_frame()
        self._check_metadata(metadata)
        # self.disabled_countries = metadata.loc[-metadata["include"], "location"].values
        # metadata = metadata[metadata["include"]].sort_values(by="location")
        return metadata

    def _check_metadata(self, df: pd.DataFrame):
        assert True
