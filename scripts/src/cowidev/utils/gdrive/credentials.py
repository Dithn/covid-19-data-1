import os

from cowidev import PATHS
from cowidev.utils.params import SECRETS


CLIENT_SECRETS_PATH = SECRETS.google.client_secrets
SETTINGS_PATH = os.path.join(PATHS.CONFIG_DIR, "gdrive_settings.yaml")
CREDENTIALS_PATH = os.path.join(PATHS.CONFIG_DIR, "gdrive_credentials.json")
