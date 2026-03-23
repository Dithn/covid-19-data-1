from cowidev.utils.params import SECRETS


def url_request_broken(url):
    url_base, url_params = url.split("query?")
    x = filter(lambda x: x[0] != "where", [p.split("=") for p in url_params.split("&")])
    params = dict(x)
    return f"{url_base}/query", params


def to_proxy_url(url):
    return f"http://api.scraperapi.com?api_key={SECRETS.scraperapi.token}&url={url}"
