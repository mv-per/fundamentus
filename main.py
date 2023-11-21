def main():
    from src.waitingbar import WaitingBar
    from src.fundamentus import get_data
    import pandas as pd

    progress_bar = WaitingBar("[*] Generating excel...")
    result = get_data()
    progress_bar.stop()


if __name__ == "__main__":
    main()
