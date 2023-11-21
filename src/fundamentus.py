#!/usr/bin/env python3
from lxml.html import fromstring
from collections import OrderedDict
import numpy as np

import requests
from src.list_stocks import get_stocks

table_headers = [
    "Papel",
    "Cotacao",
    "P/L",
    "P/VP",
    "PSR",
    "DY",
    "P/Ativo",
    "P/Cap.Giro",
    "P/EBIT",
    "P/ACL",
    "EV/EBIT",
    "EV/EBITDA",
    "Mrg.Ebit",
    "Mrg.Liq.",
    "Liq.Corr.",
    "ROIC",
    "ROE",
    "Liq.2meses",
    "Pat.Liq",
    "Div.Brut/Pat.",
    "Cresc.5anos",
]

percentuals = [
    "Cresc.5anos",
    "ROIC",
    "ROE",
    "Mrg.Ebit",
    "Mrg.Liq.",
    "DY",
]


def get_dividend_average(stock: str) -> float:
    if "1" in stock:
        url = f"https://statusinvest.com.br/fundos-imobiliarios/{stock}"
        title = "Soma total de proventos distribuídos nos últimos 12 meses"
    else:
        url = f"https://statusinvest.com.br/acoes/{stock}"
    headers = {
        "User-agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201",
        "Accept": "text/html, text/plain, text/css, text/sgml, */*;q=0.01",
    }

    response = requests.get(url, headers=headers)
    assert response.ok, f"Error fetching data from {url}"

    tree = fromstring(response.content)
    dividends = tree.xpath(
        '//div[@title="Soma total de proventos distribuídos nos últimos 12 meses"]'
    )

    if not len(dividends) > 0:
        return np.NaN

    return todecimal(dividends[0][1].text)


def get_fundamentus_data():
    """ """
    url = "http://www.fundamentus.com.br/resultado.php"
    headers = {
        "User-agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201",
        "Accept": "text/html, text/plain, text/css, text/sgml, */*;q=0.01",
    }

    response = requests.get(url, headers=headers)
    assert response.ok, f"Error fetching data from {url}"

    tree = fromstring(response.content)
    tables = tree.xpath('//table[@id="resultado"]')

    assert len(tables) == 1, "More than one result table found"

    result_table = tables[0]
    table_body = result_table.xpath("tbody")[0]
    result = OrderedDict()

    stocks = get_stocks()

    for rows in table_body.findall("tr"):
        columns = rows.findall("td")

        assert len(columns) == len(table_headers), "Size of table and header mismatch"

        stock_name = columns[0][0][0].text

        if stock_name is None or stock_name not in stocks or stock_name in result:
            continue

        row_data = {}
        for i, header in enumerate(table_headers[1:], start=1):
            row_data[header] = todecimal(columns[i].text)

        row_data["dividends"] = get_dividend_average(stock_name)

        result.update({stock_name: row_data})

    return result


def todecimal(string):
    string = string.replace(".", "")
    string = string.replace(",", ".")

    if string.endswith("%"):
        string = string[:-1]
        value = float(string) / 100
    elif string.startswith("R$ "):
        string = string[3:]
        value = float(string)
    else:
        value = float(string)

    return value


def get_data():
    import pandas as pd
    import numpy as np

    fundamentus_data = get_fundamentus_data()

    df = pd.DataFrame(fundamentus_data, columns=fundamentus_data.keys())

    df = df.transpose()

    desired_pl = 25
    desired_vpa = 1.5
    print(f"Calculating Intrinsic values: sqrt({desired_pl*desired_vpa}*P/L*P/VP)")
    df["graham"] = np.sqrt(desired_pl * desired_vpa * df["P/L"] * df["P/VP"])
    df["gragam_safety_margin"] = (df["graham"] - df["Cotacao"]) / df["graham"] * 100

    print("Calculating Bazin values: (12mo dividend average) * 100 / 5")
    df["bazin"] = df["dividends"] / 5 * 100

    df2 = df.loc[(df["bazin"] > df["Cotacao"]) & (df["gragam_safety_margin"] > 30)]
    df2.sort_values(by=["bazin", "gragam_safety_margin", "ROIC"])

    with pd.ExcelWriter("output.xlsx", engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="fundamentus_data")
        df2.to_excel(writer, sheet_name="valuations")


if __name__ == "__main__":
    get_data()
