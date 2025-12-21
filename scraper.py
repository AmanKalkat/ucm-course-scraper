from bs4 import BeautifulSoup
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
import time
import pandas as pd


class Scraper:
    def __init__(self, driver, website_url, logger=None):
        self.driver = driver
        self.soup = None
        self.website_url = website_url
        self.logger = logger

        self.all_courses = [] # list of course_data dicts
        self.external_link_classes = [] # for manual review
        self.scraped_courses = set() # set to track already-scraped course codes

    def log(self, message):
        if self.logger:
            self.logger.info(message)
        else:
            print(message)
    
    def get_course_template(self):
        return {
            "course code": None,
            "course name": None,
            "credits": None,
            "course description": None,
            "prereqs": None,
            "coreqs": None,
            "class levels": None,
            "repeats allowed for credit": None,
        }
    

    def num_pages(self):
        if self.soup is None:
            raise Exception("Soup has not been initalized. Call location_courses()")
            
        page_td = (
            self.soup
            .find_all("table", class_="table_default")[-1]
            .find_all("tr")[-1] # type: ignore
            .find_all("td")[-1] # type: ignore
        )
        
        total_pages = int(page_td.text[-2:])
        self.log(f"Total number of pages in pagination: {total_pages}.")
        return total_pages
    

    """
    Example of EC :
        element = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located(locator)
    )
    """
    def scrape(self):
        self.driver.get(self.website_url)
        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")

        time.sleep(5)
        total_pages = self.num_pages()

        for page in range(1, total_pages + 1):
            # Replace the page number in the URL (filter%5Bcpage%5D is filter[cpage] URL-encoded)
            url = self.website_url.replace("filter%5Bcpage%5D=1", f"filter%5Bcpage%5D={page}")
            self.log(f"\n=== Scraping page {page}/{total_pages} ===")
            self.log(f"URL: {url}")
            self.driver.get(url)
            
            time.sleep(2)

            last_table = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table:last-of-type"))
            )


            rows = last_table.find_elements(By.TAG_NAME, "tr")
            for row_index in range(len(rows)):

                rows = last_table.find_elements(By.TAG_NAME, "tr")
                row = rows[row_index]

                try:
                    td = row.find_element(By.CLASS_NAME, "width")
                    link_to_click = td.find_element(By.TAG_NAME, "a")
                    course_name = link_to_click.text

                    self.log(f"Clicking on: {course_name}")
                    link_to_click.click()

                    WebDriverWait(self.driver, 10).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.CLASS_NAME, "coursepadding")),
                            EC.number_of_windows_to_be(2)
                        )
                    )

                    if len(self.driver.window_handles) > 1:
                        self.log(f"  -> External link detected for {course_name}")
                        self.external_link_classes.append(course_name)
                        self.driver.switch_to.window(self.driver.window_handles[1])
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                    else:
                        # Dropdown appeared, extract the course data
                        dropdown_td = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "coursepadding"))
                        )
                        dropdown_html = dropdown_td.get_attribute("outerHTML")
                        course_data = self.parse_html(dropdown_html)

                        # Check if this course has already been scraped
                        course_code = course_data.get('course code', 'Unknown')
                        if course_code in self.scraped_courses:
                            self.log(f"  -> Skipping duplicate: {course_code}")
                        else:
                            # Add to scraped set and courses list
                            self.scraped_courses.add(course_code)
                            self.all_courses.append(course_data)
                            self.log(f"  -> Scraped: {course_code}")

                        time.sleep(0.5)

                        rows = last_table.find_elements(By.TAG_NAME, "tr")
                        row = rows[row_index]
                        td = row.find_element(By.CLASS_NAME, "width")
                        link_to_click = td.find_element(By.TAG_NAME, "a")

                        # Click again to close the dropdown
                        link_to_click.click()

                        # Wait for dropdown to close
                        WebDriverWait(self.driver, 10).until(
                            EC.invisibility_of_element_located((By.CLASS_NAME, "coursepadding"))
                        )
                        self.log(f"  -> Dropdown closed for {course_name}")

                except TimeoutException as e:
                    self.log(f"Timeout waiting for dropdown/window for row {row_index}: {e}")
                except StaleElementReferenceException as e:
                    self.log(f"Stale element for row {row_index}: {e}")
                except NoSuchElementException as e:
                    self.log(f"Element not found in row {row_index}: {e}")
                except Exception as e:
                    self.log(f"Unexpected error for row {row_index}: {type(e).__name__} - {e}")



    def parse_course_titles(self, course_soup, course_data):
        h3 = course_soup.find("h3")
        if h3 and ":" in h3.text:
            segments = h3.text.split(":", 1)
            course_data["course code"] = segments[0].strip()
            course_data["course name"] = segments[1].strip()
    
    def handle_credits(self, text, course_data): #text is prev in this case
        text.split(":")
        credits = int(text[-1])
        course_data["credits"] = credits

    def handle_credit_range(self, text, next, course_data):
        bounds = []
        
        text.split(":")
        bounds.append(int(text[-1].strip()))

        if next and next.startswith("Upper Unit Limit:"):
            bounds.append(int(next.split(":")[-1].strip()))
        
        course_data["credits"] = bounds
        
    def handle_prereqs(self, text, course_data):
        line = text.split(":", 1)[1].strip()
        line = line.replace("(", "").replace(")", "").replace("\xa0", " ").replace("\n", "")
        parts = line.split(",")
        # example from CSE 150
        #['CSE 031 or EE 060', 'CSE 100 and\n    MATH 024']
        prereqs = []
        for part in parts:
            stripped = part.strip()
            if stripped:
                if " and " in stripped:
                    for p in part.split(" and "):
                        prereqs.append(p.strip())
                else:
                    prereqs.append(stripped)
        
        course_data["prereqs"] = prereqs

    def handle_coreqs(self, text, course_data):
        line = text.split(":", 1)[1].strip()
        line = line.replace("(", "").replace(")", "").replace("\xa0", " ")
        parts = line.split(",")
            
        coreqs = []
        for part in parts:
            stripped = part.strip()
            if stripped:
                if " and " in stripped: 
                    for p in part.split(" and "):
                        coreqs.append(p.strip())
                else:
                    coreqs.append(stripped)
            
        course_data["coreqs"] = coreqs

    def handle_class_levels(self, br, course_data):
        levels = []
        ul = br.find_next("ul")

        if ul:
            for li in ul.find_all("li"):
                level = li.get_text(strip=True)
                if level:
                    levels.append(level)
        
        course_data["class levels"] = levels

    def repeats_allowed(self, text, course_data):
        line = text.split(":", 1)[1].strip()
        course_data["repeats allowed for credit"] = int(line)
    
    def fill_na_defaults(self, course_data):
        for key in course_data.keys():
            if course_data[key] == None:
                course_data[key] = "N/A"

    def parse_html(self, raw_html):
        
        course_soup = BeautifulSoup(raw_html, "html.parser")
        if not course_soup:
            raise Exception("Cannot parse page because self.soup is not initalized")
        
        course_data: dict[str, str | int | None | list[int] | list[str]] = {
            "course code": None,
            "course name": None,
            "credits": None,
            "course description": None,
            "prereqs": None,
            "coreqs": None,
            "class levels": None,
            "repeats allowed for credit": None,
        }

        self.parse_course_titles(course_soup, course_data)

        for br in course_soup.find_all("br"):
            prev = str(br.previous_sibling).strip()
            next = br.find_next(string=True)

            if prev.startswith("Units:"):
                self.handle_credits(prev, course_data)
            elif prev.startswith("Lower Unit Limit"):
                next = br.find_next(string=True)
                self.handle_credit_range(prev, next, course_data)
            
            if prev.endswith("."):
                course_data["course description"] = prev.strip()
            
            if prev.startswith("Prerequisite Courses"):
                self.handle_prereqs(prev, course_data)
            
            if prev.startswith(" Prerequisite Courses with Concurrent Option"):
                self.handle_coreqs(prev, course_data)

            if br.next_sibling and "Open only to the following class level(s):" in str(br.next_sibling):
                self.handle_class_levels(br, course_data)

            if prev.startswith("Repeats Allowed"):
                self.repeats_allowed(prev, course_data)
            
        self.fill_na_defaults(course_data)
        return course_data

    def save_to_excel(self, year, output_dir="spreadsheets"):
        os.makedirs(output_dir, exist_ok=True)
        df = pd.DataFrame(self.all_courses)

        filename = f"{output_dir}/{year}.xlsx"
        df.to_excel(filename, index=False, sheet_name="Courses")
        self.log(f"\nSaved {len(self.all_courses)} courses to {filename}")


if __name__ == "__main__":
    # Test URL for 2025-2026 classes
    catalog_25_26 = "https://catalog.ucmerced.edu/content.php?catoid=24&catoid=24&navoid=2732&filter%5Bitem_type%5D=3&filter%5Bonly_active%5D=1&filter%5B3%5D=1&filter%5Bcpage%5D=1#acalog_template_course_filter"
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    try:
        scraper = Scraper(driver, catalog_25_26)
        scraper.scrape()

        print(f"\n---------Scraping completed---------")
        print(f"Total courses scraped: {len(scraper.all_courses)}")
        print(f"External links found: {len(scraper.external_link_classes)}")

        if scraper.external_link_classes:
            print("\nExternal link classes (for manual review):")
            for link in scraper.external_link_classes:
                print(f"  - {link}")

        # Save to Excel
        scraper.save_to_excel("2025_2026")

    finally:
        driver.quit()
        print("\nDriver closed.")