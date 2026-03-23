import os

from ._config_loader import countries_mapping

__CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

# EMRO
__EMRO_CONFIG = os.path.join(__CURRENT_DIR, "emro_config.yaml")
EMRO_COUNTRIES = countries_mapping(__EMRO_CONFIG)

# ECDC
__ECDC_CONFIG = os.path.join(__CURRENT_DIR, "ecdc_config.yaml")
ECDC_COUNTRIES = countries_mapping(__ECDC_CONFIG)

# ECDC
__ACDC_CONFIG = os.path.join(__CURRENT_DIR, "acdc_config.yaml")
ACDC_COUNTRIES = countries_mapping(__ACDC_CONFIG)
