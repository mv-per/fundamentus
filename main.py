from src.reis import get_reis_data
from src.waitingbar import WaitingBar
from src.stocks import get_stocks_data


def main():
    progress_bar = WaitingBar("[*] Generating excel...")
    get_stocks_data()
    get_reis_data()
    progress_bar.stop()


if __name__ == "__main__":
    main()
