import yaml
import pandas as pd


class AnnotatorInternal:
    """Adds annotations column.

    Uses attribute `config` to add annotations. Its format should be as:

    .. code-block::

        {
            "vaccinations": [{
                'annotation_text': 'Data for China added on Jun 10',
                'location': ['World', 'Asia', 'Upper middle income'],
                'date': '2020-06-10'
            }],
            "case-tests": [{
                'annotation_text': 'something',
                'location': ['World', 'Asia', 'Upper middle income'],
                'date': '2020-06-11'
            }],
        }
    ```

    Keys in config should match those in `internal_files_columns`.
    """

    def __init__(self, config: dict):
        self.config = config

    @classmethod
    def from_yaml(cls, path):
        with open(path, "r") as f:
            dix = yaml.safe_load(f)
        return cls(dix)

    @property
    def streams(self):
        return list(self.config.keys())

    def add_annotations(self, df: pd.DataFrame, stream: str) -> pd.DataFrame:
        if stream in self.streams:
            print(f"Adding annotation for {stream}")
            return self._add_annotations(df, stream)
        return df

    def _add_annotations(self, df: pd.DataFrame, stream: str) -> pd.DataFrame:
        df = df.assign(annotations=pd.NA)
        conf = self.config[stream]
        for c in conf:
            if not ("location" in c and "annotation_text" in c):
                raise ValueError(
                    f"Missing field in {stream} (`location` and `annotation_text` are required)."
                )
            if isinstance(c["location"], str):
                mask = df.location == c["location"]
            elif isinstance(c["location"], list):
                mask = df.location.isin(c["location"])
            if "date" in c:
                mask = mask & (df.date >= c["date"])
            df.loc[mask, "annotations"] = c["annotation_text"]
        return df
