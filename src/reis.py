from typing import Dict, Any
import numpy as np
import requests
from lxml import html
import httpx
import asyncio
import time

default_request_headers = {
    "User-agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201",
    "Accept": "text/html, text/plain, text/css, text/sgml, */*;q=0.01",
}

columnHeaders = ["cod", "name"]


def get_reis() -> list[str]:
    """
    Retrieve a list of Real Estate Investments (REIs) names from a specific webpage.

    Returns:
    - list: A list of strings representing the names or symbols of Real Estate Investments.

    Raises:
    - AssertionError: If there is an error fetching data from the specified URL.

    Notes:
    - The function sends an HTTP GET request to the Clube FII website to obtain information about REIs.
    - It expects the response to be successful (status code 200).
    - The function then parses the HTML content and extracts the names or symbols of REIs from a specific table.
    - The extracted information is returned as a list.
    """
    url = "https://www.clubefii.com.br/fundo_imobiliario_lista"
    response = requests.get(url, headers=default_request_headers)

    assert response.ok, f"Error fetching data from {url}"

    tree = html.fromstring(response.content)
    table = tree.xpath(
        '//table[@class="tabela_principal sortable draggable forget-ordering"]'
    )[0]

    reis = [link.text.strip() for link in table.xpath('//a[@class="nenhuma_cor"]')]
    return reis


def parse_text(text):
    """
    Parse and convert textual representation of numeric values.

    Parameters:
    - text (str): The text to be parsed.

    Returns:
    - float or np.NaN or None: The parsed numeric value, or np.NaN if the text represents "N/A",
      or None if the resulting value is less than or equal to 1 character in length.

    Notes:
    - The function removes leading and trailing whitespaces, replaces commas with periods,
      removes currency symbols and newline characters.
    - Handles different suffixes for million (M), billion (B), and thousand (K).
    - If the text ends with '%', the function interprets it as a percentage.
    - If the text starts with 'R$', it is treated as a currency value.
    - If the text is "N/A", the function returns np.NaN.
    - If the resulting value is less than or equal to 1 character in length, the function returns None.

    Example:
    ```
    value = parse_text("R$ 1,000.50")
    if value is not None:
        print(f"Parsed Value: {value}")
    else:
        print("Invalid input for parsing.")
    ```

    """
    text = (
        text.strip()
        .replace(".", "")
        .replace(",", ".")
        .replace("R$", "")
        .replace("\n", "")
    )

    if len(text) <= 1:
        return None
    elif text.endswith("%"):
        value = float(text[:-1].strip()) / 100
    elif text.endswith(("M", "B", "K")):
        suffix = text[-1]
        multiplier = {"M": 1e6, "B": 1e8, "K": 1e3}
        value = float(text[:-1].strip()) * multiplier[suffix]
    elif text.startswith("R$ "):
        value = float(text[3:])
    elif text == "N/A":
        value = np.NaN
    else:
        value = float(text)

    return value


def get_rei_anbima_type(tree) -> str | None:
    """
    Extracts the anbiima type of Real Estate Investment (REI) from the provided HTML tree.

    Parameters:
    - tree (lxml.html.HtmlElement): The HTML tree obtained from parsing a web page.

    Returns:
    - str or None: The type of REI if found, or None if no matching information is found.

    Notes:
    - This function specifically looks for elements with the class 'basicInformation__grid__box'.
    - It filters these elements based on the presence of the text "Segmento ANBIMA" in the first paragraph.
    - If a matching element is found, the function extracts and returns the text content of the second paragraph.
    - If no matching information is found, the function returns None.
    """
    # Find all basicInformation__grid__box elements
    grid_boxes = tree.xpath('//div[@class="basicInformation__grid__box"]')

    # Filter the elements where the first p contains "Segmento ANBIMA"
    filtered_boxes = [
        box
        for box in grid_boxes
        if box.xpath('.//p[1][contains(text(), "Segmento ANBIMA")]')
    ]

    # Extract the value of the second p for filtered elements
    values = [box.xpath(".//p[2]//text()")[0].strip() for box in filtered_boxes]

    if len(values) == 1:
        return values[0]
    return None


def get_rei_type(tree) -> str | None:
    """
    Extracts the type of Real Estate Investment (REI) from the provided HTML tree.

    Parameters:
    - tree (lxml.html.HtmlElement): The HTML tree obtained from parsing a web page.

    Returns:
    - str or None: The type of REI if found, or None if no matching information is found.

    Notes:
    - This function specifically looks for elements with the class 'basicInformation__grid__box'.
    - It filters these elements based on the presence of the text "Segmento" in the first paragraph.
    - If a matching element is found, the function extracts and returns the text content of the second paragraph.
    - If no matching information is found, the function returns None.
    """

    # Find all basicInformation__grid__box elements
    grid_boxes = tree.xpath('//div[@class="basicInformation__grid__box"]')

    # Filter the elements where the first p contains "Segmento"
    filtered_boxes = [
        box for box in grid_boxes if box.xpath('.//p[1][contains(text(), "Segmento")]')
    ]

    # Extract the value of the second p for filtered elements
    values = [box.xpath(".//p[2]//text()")[0].strip() for box in filtered_boxes]

    if len(values) > 0:
        return values[0]
    else:
        return None


def handle_response(response: httpx.Response) -> Dict[str, str | float | None]:
    """
    Extracts relevant information from a web page response containing REI (Real Estate Investment) data.

    Parameters:
    - response (requests.Response): The HTTP response object obtained from a web request.

    Returns:
    - dict or None: A dictionary containing parsed REI information, including:
      - 'Ação': The stock symbol extracted from the URL.
      - 'Tipo': The general type of REI.
      - 'Tipo ANBIMA': The ANBIMA (Brazilian Financial and Capital Markets Association) type of REI.
      - 'Preço': The parsed price of the REI.
      - Other indicators and their corresponding values extracted from the web page.

    Note:
    - If the HTTP status code of the response is not 200 (OK), the function returns None.
    - The function uses the 'html.fromstring' method to parse the HTML content of the response.
    - The 'parse_text' function is assumed to be defined elsewhere for text parsing.
    """

    if response.status_code != 200:
        return

    tree = html.fromstring(response.content)

    preco = parse_text(
        tree.xpath("//div[@class='headerTicker__content__price']/p[1]//text()")[0]
    )
    indicators = tree.xpath("//div[@class='indicators__box']/p[1]//text()")

    values = tree.xpath(
        "//div[@id='indicators']/div[@class='indicators__box']/p[2]//text()"
    )
    values = [parse_text(value) for value in values if parse_text(value) is not None]

    rei_dict = dict()
    rei_dict["Ação"] = str(response.url).split("/")[-1]
    rei_dict["Tipo"] = get_rei_type(tree)
    rei_dict["Tipo ANBIMA"] = get_rei_anbima_type(tree)
    rei_dict["Preço"] = preco
    rei_dict.update(zip(indicators, values))

    return rei_dict


async def get_async(url: str) -> httpx.Response:
    """
    Asynchronously sends an HTTP GET request to the specified URL using an asynchronous HTTP client.

    Parameters:
    - url (str): The URL to send the GET request to.

    Returns:
    - httpx.Response: The response object containing the result of the GET request.

    Note:
    - Uses the httpx library for asynchronous HTTP requests.
    - The request includes default headers specified in 'default_request_headers'.
    - The 'timeout' parameter is set to None, meaning the request will not time out.

    """
    async with httpx.AsyncClient() as client:
        return await client.get(url, headers=default_request_headers, timeout=None)


async def launch(urls: list[str]) -> list[httpx.Response]:
    """
    Asynchronously launches multiple HTTP GET requests to a list of URLs.

    Parameters:
    - urls (list): A list of URLs to send GET requests to.

    Returns:
    - list: A list of httpx.Response objects containing the results of the GET requests.

    """
    resps = await asyncio.gather(*map(get_async, urls))
    return resps


def get_reis_data():
    """
    Scrapes Real Estate Investment (REI) data from the web, performs calculations,
    and generates an Excel file with the data and valuations.

    Notes:
    - Uses the functions get_reis(), launch(), and handle_response() to gather REI data.
    - Calculates Gordon values and safety margins based on specific criteria.
    - Generates an Excel file with multiple sheets containing different valuations.
    """
    import pandas as pd

    print("Scrapping reis...")

    reis = get_reis()

    print(f"{len(reis)} reis found, scrapping data...")
    urls = [f"https://www.fundsexplorer.com.br/funds/{rei}" for rei in reis]

    tm1 = time.perf_counter()
    responses = asyncio.run(launch(urls))
    tm2 = time.perf_counter()
    print(f"Data loaded... Total time elapsed: {tm2-tm1:0.2f} seconds")
    print("Parsing data...")
    data = []
    for res in responses:
        data.append(handle_response(res))

    data = [d for d in data if d is not None]

    print("Generating excel data...")

    df = pd.DataFrame.from_records(data)

    K_G = 0.1
    print(f"Calculating Gordon values: (12mo total dividends) / {K_G}")
    df["gordon"] = df["Div. por Ação"] / K_G
    df["gordon_safety_margin"] = (df["gordon"] / df["Preço"]) - 1

    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    dfs = []
    safety_margins = np.arange(50, step=10).tolist()
    safety_margins[0] = 5

    dfs = []
    for i, margin in enumerate(safety_margins):
        if i < len(safety_margins) - 1:
            upper_margin = safety_margins[i + 1]
        else:
            upper_margin = np.inf

        dfs.append(
            df.loc[
                (df["gordon_safety_margin"] > margin / 100)
                & (df["gordon_safety_margin"] < upper_margin / 100)
                & (df["Patrimônio Líquido"] > 8e5)
                & (df["Liquidez Média Diária"] > 5e5)
            ]
        )

    dfs = [
        _df.sort_values(
            by=["P/VP", "gordon_safety_margin", "Liquidez Média Diária"],
            ascending=False,
        )
        for _df in dfs
    ]

    filename = "rei_output.xlsx"

    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="fundamentus_data", index=False)
        for _df, margin in zip(dfs, safety_margins):
            _df.to_excel(writer, sheet_name=f"valuations_{margin}", index=False)

    print(f"Excel generated. File={filename}")
