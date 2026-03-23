import os
import yaml

import gdown
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from cowidev.utils.gdrive.credentials import CLIENT_SECRETS_PATH, CREDENTIALS_PATH, SETTINGS_PATH
from cowidev.utils.paths import CONFIG_DIR


def gdrive_init(encoding="utf8"):
    """From https://github.com/lucasrodes/whatstk/blob/bcb9cf7c256df1c9e270aab810b74ab0f7329436/whatstk/utils/gdrive.py#L38"""
    if not os.path.isdir(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)

    # Copy credentials to config folder
    # copyfile(client_secret_file, CLIENT_SECRETS_PATH)

    # Create settings.yaml file
    dix = {
        "client_config_backend": "file",
        "client_config_file": CLIENT_SECRETS_PATH,
        "save_credentials": True,
        "save_credentials_backend": "file",
        "save_credentials_file": CREDENTIALS_PATH,
        "get_refresh_token": True,
        "oauth_scope": [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.install",
        ],
    }
    with open(SETTINGS_PATH, "w", encoding=encoding) as f:
        yaml.dump(dix, f)

    # credentials.json
    gauth = GoogleAuth(settings_file=SETTINGS_PATH)
    gauth.CommandLineAuth()
    return gauth


def _is_gdrive_config_valid():
    if not os.path.isdir(CONFIG_DIR):
        return False
    if not os.path.isfile(CLIENT_SECRETS_PATH):
        raise ValueError(f"Credentials not found at {CLIENT_SECRETS_PATH}. Please check!")
    for f in [CREDENTIALS_PATH, SETTINGS_PATH]:
        if not os.path.isfile(f):
            return False


def get_gdrive():
    if not _is_gdrive_config_valid():
        gauth = gdrive_init()
    else:
        gauth = GoogleAuth(settings_file=SETTINGS_PATH)
    # gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    return drive


def download_folder(url, output, **kwargs):
    gdown.download_folder(url, output=output, quiet=True, use_cookies=False, **kwargs)


def download_file(url, output, **kwargs):
    gdown.download(url, output=output, **kwargs)


def list_files(parent_id):
    drive = get_gdrive()
    request = f"'{parent_id}' in parents and trashed=false"
    # Get list of files
    files = drive.ListFile({"q": request}).GetList()
    return files
