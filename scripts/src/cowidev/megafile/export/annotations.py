import yaml
import pandas as pd


class AnnotatorInternal:
    """Adds annotations column.

    Uses attribute `config` to add annotations. Its format should be as:

    ..  code-block:: python

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

    Keys in config should match those in `internal_files_columns`.
    """

    def __init__(self, config: dict, logger=None):
        self._config = config
        self._logger = logger

    @classmethod
    def from_yaml(cls, path, logger=None):
        with open(path, "r") as f:
            dix = yaml.safe_load(f)
        return cls(dix, logger)

    @property
    def config(self):
        for stream in self._config.keys():
            self._config[stream] = sorted(self._config[stream], key=lambda x: x["date"])
        return self._config

    @property
    def streams(self):
        return list(self._config.keys())

    def config_nested_to_flat(self, config):
        """Convert class attribute config to a flattened dataframe.

        Each row in the dataframe contains [stream, annotation_text, location, date]. Essentially, what gets flattened
        is the `location` field, which originally contains a list of locations.

        Args:
            config (dict): Dictionary with original class config.

        Returns:
            pd.DataFrame: Table with config in a flatten version.
        """
        data_flat = []
        for stream, config_ in config.items():
            for d in config_:
                for loc in d["location"]:
                    data_flat.append(
                        {
                            "stream": stream,
                            "annotation_text": d["annotation_text"],
                            "date": d["date"],
                            "location": loc,
                        }
                    )
        return pd.DataFrame(data_flat)

    def config_flat_to_nested(self, df_config):
        """Converts flattened config dataframe to class instance format.

        Args:
            df_config (pd.DataFrame): Flattened config.

        Returns:
            dict: Dictionary with original data.
        """
        config_nested = {}
        streams = df_config.stream.unique()
        for stream in streams:
            df_ = df_config[df_config.stream == stream]
            rec = df_.groupby(["annotation_text", "date"]).location.apply(list).reset_index().to_dict(orient="records")
            config_nested[stream] = rec
        return config_nested

    def _remove_config_duplicates(self):
        df_config = self.config_nested_to_flat(self._config)
        df_config = df_config.drop_duplicates()
        return self.config_flat_to_nested(df_config)

    def insert_annotation(self, stream: str, annotation: dict):
        # Checks
        if "annotation_text" not in annotation or "location" not in annotation or "date" not in annotation:
            raise ValueError("annotation dictionary must contain fields `annotation_text`, `location` and `date`")
        if not (
            isinstance(annotation["annotation_text"], str)
            and isinstance(annotation["location"], list)
            and isinstance(annotation["annotation_text"], str)
        ):
            raise ValueError(
                f"Check `annotation` field types. `annotation_text` (str), `location` (list) and `date` (str)"
            )
        # Add annotation
        self._config[stream].append(annotation)
        # Remove duplicates
        self._config = self._remove_config_duplicates()

    def to_yaml(self):
        pass

    def add_annotations(self, df: pd.DataFrame, stream: str) -> pd.DataFrame:
        if stream in self.streams:
            self._logger.info(f"Adding annotation for {stream}")
            return self._add_annotations(df, stream)
        return df

    def _add_annotations(self, df: pd.DataFrame, stream: str) -> pd.DataFrame:
        df = df.assign(annotations=pd.NA)
        conf = self.config[stream]
        for c in conf:
            if not ("location" in c and "annotation_text" in c):
                raise ValueError(f"Missing field in {stream} (`location` and `annotation_text` are required).")
            if isinstance(c["location"], str):
                mask = df.location == c["location"]
            elif isinstance(c["location"], list):
                mask = df.location.isin(c["location"])
            if "date" in c:
                mask = mask & (df.date >= c["date"])
            df.loc[mask, "annotations"] = c["annotation_text"]
        return df


def add_annotations_countries_100_percentage(df, annotator):
    threshold_perc = 100
    locations_exc = df[df.people_vaccinated_per_hundred > threshold_perc].groupby("location").date.min().to_dict()
    for loc, dt in locations_exc.items():
        annotator.insert_annotation(
            "vaccinations",
            {
                "annotation_text": "Exceeds 100% due to vaccination of non-residents",
                "location": [loc],
                "date": dt,
            },
        )
    return annotator
