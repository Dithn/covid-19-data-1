import yaml


class ConfigLoader:
    def __init__(self, config: dict) -> None:
        self.config = config

    @classmethod
    def from_yaml(cls, path: str):
        with open(path, "r") as f:
            config = yaml.safe_load(f)
        return cls(config)

    def countries_mapping(self):
        if "countries" not in self.config:
            return {}
        return _records_to_dict(self.config["countries"])

    def list_countries(self):
        return list(self.countries_mapping().values())


def _records_to_dict(records):
    return {record["org_name"]: record["owid_name"] for record in records}


def countries_mapping(config_path):
    """Get organization's country mapping.

    Note, only contains mappings for countries for which we source data from the organization.

    Returns:
        dict: ORG_COUNTRY_NAME -> OWID_COUNTRY_NAME
    """
    config_loader = ConfigLoader.from_yaml(config_path)
    return config_loader.countries_mapping()


def countries(config_path):
    """List countries for which we source data from the organization.

    Returns:
        list: List of countries sourced from the organization.
    """
    config_loader = ConfigLoader.from_yaml(config_path)
    return config_loader.config
