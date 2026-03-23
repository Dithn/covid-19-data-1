import os

from ._config_loader import get_org_constants, countries_mapping

__CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

# WHO
__WHO_CONFIG = os.path.join(__CURRENT_DIR, "who_config.yaml")
WHO_COUNTRIES, WHO_VACCINES = get_org_constants(__WHO_CONFIG)

# PAHO
__PAHO_CONFIG = os.path.join(__CURRENT_DIR, "paho_config.yaml")
PAHO_COUNTRIES, PAHO_VACCINES = get_org_constants(__PAHO_CONFIG)

# AFRICACDC
__AFRICACDC_CONFIG = os.path.join(__CURRENT_DIR, "acdc_config.yaml")
ACDC_COUNTRIES, ACDC_VACCINES = get_org_constants(__AFRICACDC_CONFIG)
__AFRICACDC_ALL_CONFIG = os.path.join(__CURRENT_DIR, "acdc_all_config.yaml")
ACDC_COUNTRIES_ALL = countries_mapping(__AFRICACDC_ALL_CONFIG)

# SPC
__SPC_CONFIG = os.path.join(__CURRENT_DIR, "spc_config.yaml")
SPC_COUNTRIES, SPC_VACCINES = get_org_constants(__SPC_CONFIG)

# ECDC
__ECDC_CONFIG = os.path.join(__CURRENT_DIR, "ecdc_config.yaml")
ECDC_COUNTRIES, ECDC_VACCINES = get_org_constants(__ECDC_CONFIG)
