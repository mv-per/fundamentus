import re
import urllib.request
import urllib.parse
import http.cookiejar
import requests
from lxml import html

# from lxml.html import fragment_fromstring
from collections import OrderedDict


def get_stocks() -> list[str]:
    """
    Loads a list of all stocks currently being negotiated in the b3
    """
    url = "https://www.infomoney.com.br/cotacoes/empresas-b3/"
    response = requests.get(url)

    assert response.ok, "Error fetching data from {url}"

    tree = html.fromstring(response.content)
    links = tree.xpath("//a")
    links = [
        link
        for link in links
        if "https://www.infomoney.com.br/cotacoes/b3/" in link.get("href")
    ]

    stocks = [link.text for link in links]

    def valid_stock(stock: str) -> bool:
        if stock is not None and any(["1" in stock, "3" in stock, "4" in stock]):
            return True
        return False

    stocks = [stock for stock in stocks if valid_stock(stock)]

    return stocks


if __name__ == "__main__":
    print(get_stocks())
