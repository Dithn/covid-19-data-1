import tempfile
from urllib.parse import urlparse
import pandas as pd

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context

from cowidev.utils.web.scraping import to_proxy_url


CIPHERS = "HIGH:!DH:!aNULL:DEFAULT@SECLEVEL=1"


def read_xlsx_from_url(
    url: str,
    timeout=30,
    as_series: bool = False,
    verify=True,
    drop=False,
    ciphers_low=False,
    use_proxy=False,
    headers=None,
    **kwargs,
) -> pd.DataFrame:
    """Download and load xls file from URL.

    Args:
        url (str): File url.
        as_series (bol): Set to True to return a pandas.Series object. Source file must be of shape 1xN (1 row, N
                            columns). Defaults to False.
        kwargs: Arguments for pandas.read_excel.

    Returns:
        pandas.DataFrame: Data loaded.
    """
    with tempfile.NamedTemporaryFile() as tmp:
        download_file_from_url(
            url,
            tmp.name,
            timeout=timeout,
            verify=verify,
            ciphers_low=ciphers_low,
            use_proxy=use_proxy,
            headers=headers,
        )
        df = pd.read_excel(tmp.name, **kwargs)
    if as_series:
        return df.T.squeeze()
    if drop:
        df = df.dropna(how="all")
    return df


def read_csv_from_url(url, timeout=30, verify=True, ciphers_low=False, use_proxy=False, **kwargs):
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        download_file_from_url(
            url, tmp.name, timeout=timeout, verify=verify, ciphers_low=ciphers_low, use_proxy=use_proxy
        )
        df = pd.read_csv(tmp.name, **kwargs)
    # df = df.dropna(how="all")
    return df


def download_file_from_url(
    url,
    save_path,
    chunk_size=1024 * 1024,
    timeout=30,
    verify=True,
    ciphers_low=False,
    use_proxy=False,
    headers=None,
):
    if use_proxy:
        url = to_proxy_url(url)
    if ciphers_low:
        base_url = get_base_url(url)
        s = requests.Session()
        s.mount(base_url, DESAdapter())
        r = s.get(url, headers=headers)
    else:
        r = requests.get(url, stream=True, timeout=timeout, verify=verify, headers=headers)
    with open(save_path, "wb") as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            fd.write(chunk)


class DESAdapter(HTTPAdapter):
    """
    A TransportAdapter that re-enables 3DES support in Requests.

    From: https://stackoverflow.com/a/46186957/5056599
    """

    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=CIPHERS)
        kwargs["ssl_context"] = context
        return super(DESAdapter, self).init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=CIPHERS)
        kwargs["ssl_context"] = context
        return super(DESAdapter, self).proxy_manager_for(*args, **kwargs)


def get_base_url(url: str, scheme="https") -> str:
    """
    Parse a URL and return the base URL.

    ## Parameters :

            url: str
                URL to parse.
                <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
            scheme : {'http', 'https'}, default 'https'
                Scheme to use.

    ## Returns :

            Base URL: str
                <scheme>://<netloc>/
    """

    if scheme not in ["http", "https"]:
        raise ValueError("Invalid scheme: {}".format(scheme))
    elif scheme == "http":
        return f"http://{urlparse(url).netloc}"
    else:
        return f"https://{urlparse(url).netloc}"
