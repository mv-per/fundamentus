def main():
    from src.waitingbar import WaitingBar
    from src.fundamentus import get_data

    progress_bar = WaitingBar("[*] Generating excel...")
    get_data()
    progress_bar.stop()


if __name__ == "__main__":
    main()
