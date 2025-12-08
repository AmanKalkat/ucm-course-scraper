from scraper import Scraper
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import logging
import os

CATALOGS: dict[str, str] = {
    "2022_2023": "https://catalog.ucmerced.edu/content.php?catoid=21&catoid=21&navoid=1993&filter%5Bitem_type%5D=3&filter%5Bonly_active%5D=1&filter%5B3%5D=1&filter%5Bcpage%5D=1#acalog_template_course_filter",
    "2023_2024": "https://catalog.ucmerced.edu/content.php?catoid=22&catoid=22&navoid=2224&filter%5Bitem_type%5D=3&filter%5Bonly_active%5D=1&filter%5B3%5D=1&filter%5Bcpage%5D=1#acalog_template_course_filter",
    "2024_2025": "https://catalog.ucmerced.edu/content.php?catoid=23&catoid=23&navoid=2517&filter%5Bitem_type%5D=3&filter%5Bonly_active%5D=1&filter%5B3%5D=1&filter%5Bcpage%5D=1#acalog_template_course_filter",
    "2025_2026": "https://catalog.ucmerced.edu/content.php?catoid=24&catoid=24&navoid=2732&filter%5Bitem_type%5D=3&filter%5Bonly_active%5D=1&filter%5B3%5D=1&filter%5Bcpage%5D=1#acalog_template_course_filter",
}

def setup_logger(year: str) -> logging.Logger:
    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger(year)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    file_handler = logging.FileHandler(f"logs/{year}.log", mode='w')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.propagate = False

    return logger


def scrape_catalog(year: str, url: str) -> tuple[str, Scraper]:
    print(f"\n[{year}] Starting scraper...")
    logger = setup_logger(year)

    # ChromeDriver options
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    try:
        scraper = Scraper(driver, url, logger=logger)
        scraper.scrape()

        print(f"\n[{year}] Scraping completed!")
        print(f"[{year}] Total courses scraped: {len(scraper.all_courses)}")
        print(f"[{year}] External links found: {len(scraper.external_link_classes)}")

        if scraper.external_link_classes:
            print(f"\n[{year}] External link classes (for manual review):")
            for link in scraper.external_link_classes:
                print(f"  - {link}")

        return year, scraper

    finally:
        driver.quit()
        print(f"[{year}] Driver closed.")


def main():
    num_workers: int = 4
    print(f"\nScraping {len(CATALOGS)} UCM course catalogs.")
    print(f'Using {num_workers} worker threads.')

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {}
        for year, url in CATALOGS.items():
            future = executor.submit(scrape_catalog, year, url)
            futures[future] = year

        results = {}

        for future in as_completed(futures):
            year = futures[future]
            try:
                year, scraper = future.result()
                results[year] = scraper
                print(f"\n O[{year}] Successfully completed")

            except Exception as e:
                print(f"\n X [{year}] Error: {e}")

    print("\nSaving results to Excel files...")

    for year, scraper in results.items():
        try:
            scraper.save_to_excel(year)
            print(f" O [{year}] Excel file saved successfully")
        except Exception as e:
            print(f" X [{year}] Error saving Excel: {e}")

    print("\nFINAL SUMMARY")
    for year, scraper in results.items():
        print(f"{year}: {len(scraper.all_courses)} courses scraped")


if __name__ == "__main__":
    time_file = open("time_elapsed.txt", "w")

    start_time = time.time()
    main()
    end_time = time.time()

    time_elapsed = end_time - start_time
    time_file.write(f"{time_elapsed}")
    time_file.close()

    print(f"\nTotal time elapsed: {time_elapsed:.3f} seconds")
