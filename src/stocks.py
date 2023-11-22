#!/usr/bin/env python3
from lxml.html import fromstring
from collections import OrderedDict
import numpy as np
import pandas as pd

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

default_request_headers = {
    "User-agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201",
    "Accept": "text/html, text/plain, text/css, text/sgml, */*;q=0.01",
}


def to_float(text: str) -> float:
    """
    Converts a formatted string representing a numeric value into a float.

    Parameters:
    - text (str): The input string representing a numeric value. It may include formatting such as
      commas, periods, currency symbols, or percentage signs.

    Returns:
    - float: The numeric value represented by the input string after formatting conversion.

    This function takes a string as input, cleans up common formatting elements such as commas and periods,
    and then converts the string into a float. It handles various cases, including percentage values and
    currency symbols.

    If the input string ends with a percentage sign, it is converted to a decimal value. If the string starts
    with "R$ ", indicating a currency symbol, it removes the symbol before conversion.

    Examples:
    - "1,234.56" => 1234.56
    - "5%" => 0.05
    - "R$ 1,000" => 1000.0

    Note: This function assumes that the input string is appropriately formatted for conversion,
    and unexpected formats may result in errors.
    """
    text = text.replace(".", "")
    text = text.replace(",", ".")

    if text.endswith("%"):
        text = text[:-1]
        value = float(text) / 100
    elif text.startswith("R$ "):
        text = text[3:]
        value = float(text)
    else:
        value = float(text)

    return value


def get_dividend_average(stock: str) -> float:
    """
    Retrieves and calculates the average dividend yield for a given stock or real estate investment trust (REIT)
    by scraping data from StatusInvest, a Brazilian financial website.

    Parameters:
    - stock (str): The stock symbol or REIT code for which the dividend yield is to be retrieved.

    Returns:
    - float: The average dividend yield over the last 12 months, or NaN if the information is not available.

    The function first constructs a URL based on the provided stock symbol, distinguishing between stocks and REITs.
    It then sends an HTTP request to the StatusInvest website, using a custom User-agent header to simulate a
    web browser. After obtaining the response, it parses the HTML content and extracts the total dividends distributed
    over the last 12 months.

    If the data is successfully retrieved, the function returns the calculated average dividend yield as a float.
    If the data is not available or if an error occurs during the process, the function returns NaN.

    Note: This function relies on web scraping, and any changes to the website's structure may affect its functionality.
    """

    if "1" in stock:
        url = f"https://statusinvest.com.br/fundos-imobiliarios/{stock}"
    else:
        url = f"https://statusinvest.com.br/acoes/{stock}"

    response = requests.get(url, headers=default_request_headers)

    if not response.ok:
        print("Error fetching data from {url}")
        return np.NaN

    tree = fromstring(response.content)
    dividends = tree.xpath(
        '//div[@title="Soma total de proventos distribuídos nos últimos 12 meses"]'
    )

    if not len(dividends) > 0:
        return np.NaN

    return to_float(dividends[0][1].text)


def scrape_stock_data() -> OrderedDict:
    """
    Scrapes financial data for various stocks from the Fundamentus website (http://www.fundamentus.com.br).

    Returns:
    - OrderedDict: A dictionary containing financial data for each stock, including key metrics such as
      earnings, dividends, and other relevant information. The data is organized with stock names as keys.

    This function performs web scraping on the Fundamentus website to gather financial data for a list of stocks.
    It sends an HTTP request to the specified URL, fetches the result table, and extracts relevant information.

    The function ensures there is exactly one result table, fetches the headers, and iterates through each row
    to collect data for individual stocks. The data includes metrics like earnings, dividends, and others.

    Additionally, it utilizes helper functions like 'get_stocks' to obtain a list of stocks and 'get_dividend_average'
    to calculate the average dividend yield for each stock.

    The final result is an OrderedDict containing comprehensive financial data for each stock, organized by stock names.

    Note: This function relies on web scraping, and any changes to the website's structure may affect its functionality.
    """

    url = "http://www.fundamentus.com.br/resultado.php"

    response = requests.get(url, headers=default_request_headers)
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
            row_data[header] = to_float(columns[i].text)

        row_data["dividends"] = get_dividend_average(stock_name)

        result.update({stock_name: row_data})

    return result


def get_stocks_data(load_new_data: bool = False) -> None:
    """
    Gathers financial data from the Fundamentus website, performs valuation calculations,
    and outputs the results to an Excel file.

    The function utilizes the 'get_fundamentus_data' function to obtain financial data for various stocks.
    It then creates a Pandas DataFrame from the collected data, transposes it, and performs valuation
    calculations based on desired price-to-earnings (P/E) and price-to-book value (P/B) ratios.

    The calculated intrinsic values using the Graham formula are stored in the 'graham' column, and
    safety margins are computed. Additionally, Bazin values are calculated based on the 12-month average
    dividend yield.

    The resulting DataFrame is filtered based on criteria such as Bazin values being higher than the current
    stock price and a safety margin greater than 30%. The filtered DataFrame is then sorted by Bazin values,
    safety margin, and return on invested capital (ROIC).

    The final results, including the original and filtered DataFrames, are exported to an Excel file named "output.xlsx"
    with two sheets: "fundamentus_data" and "valuations".

    Note: This function relies on external functions such as 'get_fundamentus_data', and any changes to
    their behavior or the website's structure may affect the functionality of this function.
    """
    filename = "output.xlsx"

    if load_new_data:
        fundamentus_data = scrape_stock_data()
        df = pd.DataFrame(fundamentus_data, columns=fundamentus_data.keys())
        df = df.transpose()
        df.rename(columns={"Unnamed: 0": "Papel"})
    else:
        print(f"loading dataframe from {filename}")
        df = pd.read_excel(open(filename, "rb"), sheet_name="fundamentus_data")
        # df = df.rename(columns={"Unnamed: 0": "Papel"})
        # df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    calculate_indicators(df)

    safety_margins = [5, 10, 20, 30, 40]

    dfs = []
    for margin in safety_margins:
        dfs.append(filter_stocks(df, margin))

    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        workbook = writer.book
        percentage_format = workbook.add_format({"num_format": "0%"})

        df.to_excel(writer, sheet_name="fundamentus_data", index=False)
        for _df, margin in zip(dfs, safety_margins):
            _df.to_excel(writer, sheet_name=f"valuations_{margin}", index=False)

        for margin in safety_margins:
            worksheet = writer.sheets[f"valuations_{margin}"]
            for col in [5, 6, 10, 11, 12]:
                worksheet.set_column(col - 1, col - 1, None, percentage_format)


def filter_stocks(dataframe: pd.DataFrame, margin: int | float) -> pd.DataFrame:
    """
    Filters stocks based on safety margins and returns a DataFrame with selected financial metrics.

    Parameters:
    - dataframe (pd.DataFrame): The input Pandas DataFrame containing stock data.
    - margin (int | float): The safety margin threshold for filtering stocks.

    Returns:
    - pd.DataFrame: A filtered DataFrame containing selected financial metrics for stocks
      with safety margins above the specified threshold.
    """
    dataframe.replace([np.inf, -np.inf], np.nan, inplace=True)
    new_dataframe = dataframe.loc[
        (dataframe["bazin_safety_margin"] > margin / 100)
        & (dataframe["graham_safety_margin"] > margin / 100)
    ]

    new_dataframe = new_dataframe[
        [
            "Papel",
            "Cotacao",
            "P/L",
            "P/VP",
            "ROIC",
            "EY",
            "graham",
            "bazin",
            "gordon",
            "graham_safety_margin",
            "bazin_safety_margin",
            "gordon_safety_margin",
        ]
    ]

    new_dataframe = new_dataframe.sort_values(by=["ROIC", "EY"], ascending=False)

    return new_dataframe


def calculate_indicators(dataframe: pd.DataFrame) -> None:
    """
    Calculates financial indicators and adds them to the provided DataFrame.

    Parameters:
    - dataframe (pd.DataFrame): The input Pandas DataFrame containing stock data.

    Returns:
    - None: The function modifies the input DataFrame in-place.

    Functionality:
    1. Calculates Earnings Yield (EY) as the inverse of EV/EBIT (Enterprise Value to Earnings Before Interest and Taxes).
    2. Calculates Graham Intrinsic values using the formula: sqrt(desired_pl * desired_vpa * P/L * P/VP).
    3. Computes the safety margin for Graham valuation as (Intrinsic Value / Current Price).
    4. Calculates Bazin values based on the 12-month average dividend yield.
    5. Computes the safety margin for Bazin valuation as (Bazin Value / Current Price).
    """
    dataframe["Pat.Liq"] = dataframe["Pat.Liq"] / 1000
    print("Calculating EY (Earnings Yield = EBIT/Enterprise Value)")
    dataframe["EY"] = 1 / dataframe["EV/EBIT"]
    dataframe["LPA"] = dataframe["Cotacao"] / dataframe["P/L"]
    dataframe["VPA"] = dataframe["Cotacao"] / dataframe["P/VP"]

    desired_pl = 25
    desired_vpa = 1.5

    print(
        f"Calculating Graham Intrinsic values: sqrt({desired_pl*desired_vpa}*LPA*VPA)"
    )
    dataframe["graham"] = np.sqrt(
        desired_pl * desired_vpa * dataframe["LPA"] * dataframe["VPA"]
    )
    dataframe["graham_safety_margin"] = (dataframe["graham"] / dataframe["Cotacao"]) - 1

    print("Calculating Bazin values: (12mo dividend average) * 100 / 5")
    dataframe["bazin"] = dataframe["dividends"] / 5 * 100
    dataframe["bazin_safety_margin"] = (dataframe["bazin"] / dataframe["Cotacao"]) - 1

    above_average_dividend = 4 / 100
    safety_margin = 20
    safety_rate = 1 + (safety_margin / 100)
    print(
        "Calculating Gordon values: 12*(12mo dividend average) / ([above_average_dividend * safety_rate] - 0)"
    )
    dataframe["gordon"] = (
        12 * dataframe["dividends"] / (above_average_dividend * safety_rate - 0)
    )
    dataframe["gordon_safety_margin"] = (dataframe["gordon"] / dataframe["Cotacao"]) - 1


if __name__ == "__main__":
    get_data()
