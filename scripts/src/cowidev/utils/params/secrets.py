import os
from dataclasses import dataclass, field

from pyaml_env import parse_config

from cowidev.utils.paths import SECRETS_FILE


if os.path.isfile(SECRETS_FILE):
    secrets_raw = parse_config(SECRETS_FILE, raise_if_na=False)
else:
    secrets_raw = {}


@dataclass()
class GoogleSecrets:
    client_secrets: str = ""
    mail: str = None


@dataclass()
class ScraperAPISecrets:
    token: str = ""


@dataclass()
class SlackSecrets:
    token: str = ""


@dataclass()
class VaccinationsSecrets:
    post: str = None
    sheet_id: str = None


@dataclass()
class TestingSecrets:
    post: str = None
    sheet_id: str = None
    sheet_id_attempted: str = None


@dataclass()
class TwitterSecrets:
    consumer_key: str = None
    consumer_secret: str = None
    access_secret: str = None
    access_token: str = None


@dataclass()
class Secrets:
    google: GoogleSecrets = field(default_factory=dict)
    scraperapi: ScraperAPISecrets = field(default_factory=dict)
    slack: SlackSecrets = field(default_factory=dict)
    vaccinations: VaccinationsSecrets = field(default_factory=dict)
    testing: TestingSecrets = field(default_factory=dict)
    twitter: TwitterSecrets = field(default_factory=dict)

    def __post_init__(self):
        self.google = GoogleSecrets(**self.google)
        self.scraperapi = ScraperAPISecrets(**self.scraperapi)
        self.slack = SlackSecrets(**self.slack)
        self.vaccinations = VaccinationsSecrets(**self.vaccinations)
        self.testing = TestingSecrets(**self.testing)
        self.twitter = TwitterSecrets(**self.twitter)


# config_raw["global_"] = config_raw.pop("global")
SECRETS = Secrets(**secrets_raw)
