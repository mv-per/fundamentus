# Stock Valuation Tool

## Overview

This Python script serves as a stock valuation tool, collecting financial data from the Fundamentus and StatusInvest websites and performing valuation calculations. It includes functions for web scraping, data manipulation, and valuation metrics calculation.

## Functions

### `get_dividend_average(stock: str) -> float`

This function retrieves the average dividend yield for a given stock by scraping data from the StatusInvest website. It takes a stock symbol as input and returns the calculated average dividend yield over the last 12 months.

### `scrape_stock_data() -> OrderedDict`

The `scrape_stock_data` function performs web scraping on the Fundamentus website (http://www.fundamentus.com.br) to gather financial data for various stocks. It returns an `OrderedDict` containing comprehensive financial data for each stock, organized by stock names.

### `to_float(string: str) -> float`

The `to_float` function converts a formatted string representing a numeric value into a float. It handles various formatting elements such as commas, periods, currency symbols, and percentage signs.

### `get_data()`

The `get_data` function utilizes the previously mentioned functions to gather financial data, perform valuation calculations, and output the results to an Excel file. It calculates intrinsic values using the Graham formula, safety margins, and Bazin values based on the 12-month average dividend yield.

## Dependencies

- [Python](https://www.python.org/)
- [Pandas](https://pandas.pydata.org/)
- [NumPy](https://numpy.org/)
- [Requests](https://docs.python-requests.org/en/latest/)
- [Lxml](https://lxml.de/)

## Usage

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Run the code:

```bash
python main.py
```

## Note

This tool relies on web scraping, and any changes to the websites' structure may affect its functionality.
Ensure that you comply with the terms of use of the websites from which the data is scraped.
