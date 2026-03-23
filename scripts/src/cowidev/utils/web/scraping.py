import json
import requests

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChroOpt
from selenium.webdriver.firefox.options import Options as FireOpt

from cowidev.utils.web.utils import to_proxy_url


def get_headers() -> dict:
    """Get generic header for requests.

    Returns:
        dict: Header.
    """
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.16; rv:86.0) Gecko/20100101 Firefox/86.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "*",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }


def get_response(
    source: str,
    request_method: str = "get",
    use_proxy: bool = False,
    **kwargs,
):
    source_orig = source
    kwargs["headers"] = kwargs.get("headers", get_headers())
    kwargs["verify"] = kwargs.get("verify", True)
    kwargs["timeout"] = kwargs.get("timeout", 20)
    if use_proxy:
        source = to_proxy_url(source)
    try:
        if request_method == "get":
            response = requests.get(source, **kwargs)
        elif request_method == "post":
            response = requests.post(source, **kwargs)
        else:
            raise ValueError(f"Invalid value for `request_method`: {request_method}. Use 'get' or 'post'")
    except Exception as err:
        raise err
    if not response.ok:
        scrapapi_used = "Scraper API was used!\n" if use_proxy else ""
        raise ValueError(
            f"Source {source_orig} not reached! {scrapapi_used}Error code {response.status_code} {response.reason}"
            # +": {response.content}",
        )
    return response


def get_soup(
    source: str,
    from_encoding: str = None,
    # parser="html.parser",
    parser="lxml",
    request_method: str = "get",
    use_proxy: bool = False,
    **kwargs,
) -> BeautifulSoup:
    """Get soup from website.

    Args:
        source (str): Website url.
        from_encoding (str, optional): Encoding to use. Defaults to None.
        parser (str, optional): HTML parser. Read https://www.crummy.com/software/BeautifulSoup/bs4/doc/
                                #installing-a-parser. Defaults to 'lxml'.
        request_method (str, optional): Request method. Options are 'get' and 'post'. Defaults to GET method. For POST
                                        method, make sure to specify a header (default one does not work).
        use_proxy(bool):
        kwargs (dict): Extra arguments passed to requests.get method. Default values for `headers`, `verify` and
                        `timeout` are used.
    Returns:
        BeautifulSoup: Website soup.
    """
    response = get_response(source, request_method, use_proxy, **kwargs)
    content = response.text
    soup = BeautifulSoup(content, parser, from_encoding=from_encoding)
    if soup.text == "":
        soup = BeautifulSoup(content, "html.parser", from_encoding=from_encoding)
    # print(response.url)
    return soup


def request_json(url, mode="soup", **kwargs) -> dict:
    """Get data from `url` as a dictionary.

    Content at `url` should be a dictionary.

    Args:
        url (str): URL to data.
        mode (str): Mode to use. Accepted is 'soup' (default) and 'raw'.
        kwargs: Check `get_soup` for the complete list of accepted arguments.

    Returns:
        dict: Data
    """
    if mode == "soup":
        text = request_text(url, **kwargs)
        return json.loads(text)
    elif mode == "raw":
        return get_response(url, **kwargs).json()
    raise ValueError(f"Unrecognized `mode` value: {mode}. Accepted values are 'soup' and 'raw'.")


def request_text(url, mode="soup", **kwargs) -> str:
    """Get data from `url` as plain text.

    Content at `url` should be a dictionary.

    Args:
        url (str): URL to data.
        mode (str): Mode to use. Accepted is 'soup' (default) and 'raw'.
        kwargs: Check `get_soup` for the complete list of accepted arguments.

    Returns:
        dict: Data
    """
    if mode == "soup":
        soup = get_soup(url, **kwargs)
        return soup.text
    elif mode == "raw":
        return get_response(url, **kwargs).text
    raise ValueError(f"Unrecognized `mode` value: {mode}. Accepted values are 'soup' and 'raw'.")


def sel_options(headless: bool = True, firefox: bool = False):
    if firefox:
        op = FireOpt()
    else:
        op = ChroOpt()
        op.add_experimental_option(
            "prefs",
            {
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
            },
        )
    op.add_argument("--disable-notifications")
    if headless:
        op.add_argument("--headless")
    return op


def get_driver(
    headless: bool = True, download_folder: str = None, options=None, firefox: bool = False, timeout: int = None
):
    if options is None:
        options = sel_options(headless=headless, firefox=firefox)
    if firefox:
        driver = webdriver.Firefox(options=options)
    else:
        driver = webdriver.Chrome(options=options)
    if download_folder:
        set_download_settings(driver, download_folder, firefox)
    if timeout is not None:
        driver.set_page_load_timeout(timeout)
    return driver


def set_download_settings(driver, folder_name: str = None, firefox: bool = False):
    if firefox:
        raise NotImplementedError("Download capabilities only supported for Chromedriver!")
    if folder_name is None:
        folder_name = "/tmp"
    driver.command_executor._commands["send_command"] = (
        "POST",
        "/session/$sessionId/chromium/send_command",
    )
    params = {
        "cmd": "Page.setDownloadBehavior",
        "params": {"behavior": "allow", "downloadPath": folder_name},
    }
    _ = driver.execute("send_command", params)


def scroll_till_element(driver, element):
    desired_y = (element.size["height"] / 2) + element.location["y"]
    current_y = (driver.execute_script("return window.innerHeight") / 2) + driver.execute_script(
        "return window.pageYOffset"
    )
    scroll_y_by = desired_y - current_y
    driver.execute_script("window.scrollBy(0, arguments[0]);", scroll_y_by)
