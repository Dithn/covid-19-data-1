from cowidev.hosp.sources import __all__ as countries


# Import modules
country_to_module = {c: f"cowidev.hosp.sources.{c}" for c in countries}
MODULES_NAME = list(country_to_module.values())
