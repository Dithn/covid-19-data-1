from dataclasses import dataclass
from pyaml_env import parse_config

from cowidev.utils.paths import CONFIG_FILE
from cowidev.utils.exceptions import ConfigFileError


config_raw = parse_config(CONFIG_FILE, raise_if_na=False)
if config_raw is None:
    raise ConfigFileError(f"Empty configuration file! Check content from {CONFIG_FILE}.")


@dataclass()
class VaccinationsProcessConfig:
    skip_complete: list
    skip_monotonic_check: list
    skip_anomaly_check: list


@dataclass()
class BaseGetConfig:
    countries: list
    skip_countries: list


@dataclass()
class TestingGetConfig(BaseGetConfig):
    pass


@dataclass()
class VaccinationsGetConfig(BaseGetConfig):
    pass


@dataclass()
class HospitalizationsGenerateConfig(BaseGetConfig):
    pass


@dataclass()
class Base4Config:
    get: BaseGetConfig
    process: dict
    generate: dict
    export: dict


@dataclass()
class TestingConfig(Base4Config):
    get: TestingGetConfig

    def __post_init__(self):
        if self.get["countries"] is None:
            self.get["countries"] = ["all"]
        if self.get["skip_countries"] is None:
            self.get["skip_countries"] = []
        self.get = TestingGetConfig(**self.get)


@dataclass()
class VaccinationsConfig(Base4Config):
    get: VaccinationsGetConfig
    process: VaccinationsProcessConfig

    def __post_init__(self):
        # Get
        if self.get["countries"] is None:
            self.get["countries"] = ["all"]
        if self.get["skip_countries"] is None:
            self.get["skip_countries"] = []
        self.get = VaccinationsGetConfig(**self.get)
        # Process
        if self.process["skip_complete"] is None:
            self.process["skip_complete"] = []
        if self.process["skip_monotonic_check"] is None:
            self.process["skip_monotonic_check"] = {}
        if self.process["skip_anomaly_check"] is None:
            self.process["skip_anomaly_check"] = {}
        self.process = VaccinationsProcessConfig(**self.process)


@dataclass()
class HospitalizationsConfig:
    generate: HospitalizationsGenerateConfig

    def __post_init__(self):
        # Generate
        if self.generate["countries"] is None:
            self.generate["countries"] = ["all"]
        if self.generate["skip_countries"] is None:
            self.generate["skip_countries"] = []
        self.generate = HospitalizationsGenerateConfig(**self.generate)


@dataclass()
class PipelineConfig:
    testing: TestingConfig
    vaccinations: VaccinationsConfig
    hospitalizations: HospitalizationsConfig

    def __post_init__(self):
        self.testing = TestingConfig(**self.testing)
        self.vaccinations = VaccinationsConfig(**self.vaccinations)
        self.hospitalizations = HospitalizationsConfig(**self.hospitalizations)


@dataclass()
class ExecutionConfig:
    parallel: bool
    njobs: int


@dataclass()
class Config:
    pipeline: PipelineConfig
    execution: ExecutionConfig

    def __post_init__(self):
        self.pipeline = PipelineConfig(**self.pipeline)
        self.execution = ExecutionConfig(**self.execution)


# config_raw["global_"] = config_raw.pop("global")
try:
    CONFIG = Config(**config_raw)
except TypeError as e:
    err_msg = (
        f"The format of the configuration file is not correct! Please check file {CONFIG_FILE} that it contains all"
        " required fields. Original raised error was: "
        + str(e)
    )
    raise ConfigFileError(err_msg)
