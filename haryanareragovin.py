import logging
import time
import random
import sys
import argparse
import json
import pandas as pd
from models.items import ProjectItem
from parsel import Selector
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p"
)


def get_driver(headless=True):
    """
    return: web driver
    """
    options = webdriver.ChromeOptions()
    options.headless = headless
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--disable-notifications")
    try:
        # change driver path respectively 
        return webdriver.Chrome(executable_path="C:/chromedriver.exe", options=options)
    except:
        return webdriver.Chrome(executable_path="./chromedriver", options=options)


def save_data(data):
    """
    store data to csv
    """
    ofile = district_name + "_rera_data.csv"
    try:
        pd.DataFrame(data).to_csv(ofile, index=None)
        sys.exit(f"Saved data in {ofile}")
    except Exception as e:
        logging.exception("Something went wrong while writing data")
        sys.exit(f"Exiting. Something went wrong while writing data to {ofile}")


def process_table(table_text):
    table_selector = Selector(text=table_text)
    page_driver = get_driver(headless=False)
    data = []
    for tr in table_selector.css("tbody > tr"):
        project_url = tr.css("th:nth-child(2) > a::attr(href)").get()
        if project_url:
            logging.info(f"Parsing: {project_url}")
            page_driver.get(project_url)
            page_driver.implicitly_wait(random.uniform(3, 5))
            try:
                admindiv = page_driver.find_element_by_css_selector(
                    "div#admindiv"
                ).get_attribute("innerHTML")
            except (NoSuchElementException, Exception):
                admindiv = '<table id="table"><tbody></tbody></table><br><table id="table"><tbody></tbody></table>'
        else:
            project_url = tr.css("th:nth-child(2)::text").get()
            admindiv = '<table id="table"><tbody></tbody></table><br><table id="table"><tbody></tbody></table>'
        detail_tables = Selector(text=admindiv).css("#table > tbody")
        ah_form_url = (
            detail_tables[1].css("td:nth-child(13) > a::attr(href)").get()
            or tr.css("th:nth-child(10) > a::attr(href)").get()
            or tr.css("th:nth-child(10)::text").get()
        )
        data.append(
            ProjectItem(
                project_id=detail_tables[1]
                .css("td:nth-child(2)::text")
                .get(default=""),
                url=project_url,
                name=tr.css("th:nth-child(3)::text").get(default="").title(),
                registration_number=tr.css("th:nth-child(4)::text").get(default=""),
                promoter_name=tr.css("th:nth-child(5)::text").get(default="").title(),
                address=" ".join(tr.css("th:nth-child(6) ::text").getall()).title(),
                district=tr.css("th:nth-child(7)::text").get(default=""),
                tehsil=detail_tables[0].css("td:nth-child(4)::text").get(default=""),
                registered_with=tr.css("th:nth-child(8)::text").get(default=""),
                certificate_url=tr.css("th:nth-child(9) > a::attr(href)").get()
                or tr.css("th:nth-child(9)::text").get(),
                ah_form_url=ah_form_url,
                receiving_date=detail_tables[1]
                .css("td:nth-child(3)::text")
                .get(default=""),
                online_submission_date=detail_tables[1]
                .css("td:nth-child(4)::text")
                .get(default=""),
                current_status=detail_tables[1]
                .css("td:nth-child(5)::text")
                .get(default=""),
                next_date_of_hearing=detail_tables[1]
                .css("td:nth-child(6)::text")
                .get(default=""),
                notice_dispatched=detail_tables[1]
                .css("td:nth-child(7)::text")
                .get(default=""),
                notice_dispatched_on=detail_tables[1]
                .css("td:nth-child(8)::text")
                .get(default=""),
                notice_tracking_id=detail_tables[1]
                .css("td:nth-child(9)::text")
                .get(default=""),
                notice_dispatched_remarks=detail_tables[1]
                .css("td:nth-child(10)::text")
                .get(default=""),
                view_notice=detail_tables[1]
                .css("td:nth-child(11)::text")
                .get(default=""),
                initially_scrutinized_remarks=detail_tables[1]
                .css("td:nth-child(12)::text")
                .get(default=""),
            )
        )
        if "_preview" in ah_form_url.lower():
            time.sleep(random.uniform(2, 3))
            logging.info(f"Navigating to AH Form: {project_url}")
            page_driver.get(ah_form_url)
            time.sleep(random.uniform(2, 3))
        else:
            logging.info(f"AH Form: {project_url}")
            continue
        time.sleep(random.uniform(3, 5))
    page_driver.close()
    if data:
        save_data(data=data)
    else:
        logging.info("Data list is empty")
        sys.exit()


def actions(driver, city):
    """
    Interact with form
    """
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "select[aria-controls='compliant_hearing']")
        )
    )
    driver.find_element_by_xpath('//button[@id="defaultOpen"]').click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "select#district > option:nth-child(2)")
        )
    )
    get_cities = driver.find_element_by_xpath("//select[@id='district']")
    district_names = [
        dist.text.strip() for dist in get_cities.find_elements_by_tag_name("option")[1:]
    ]
    with open("districts.json", "w") as dist_file:
        json.dump(
            {"districts": district_names}, dist_file, indent=4, ensure_ascii=False
        )
    for city_option in get_cities.find_elements_by_tag_name("option")[1:]:
        if city.upper() in city_option.text:
            city_option.click()
            logging.info(f"Selected city: {city_option.text}")
            break
    driver.implicitly_wait(random.uniform(0, 2))
    driver.find_element_by_xpath("//button[@name='basic_search']").click()
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#compliant_hearing > tbody > tr:nth-child(2)")
            )
        )
    except (TimeoutException, Exception):
        sys.exit("No data available in table")
    time.sleep(random.uniform(3, 5))
    entries_per_page = driver.find_element_by_xpath(
        "//select[@aria-controls='compliant_hearing']"
    )
    entries_per_page.find_elements_by_tag_name("option")[-1].click()
    table = driver.find_element_by_css_selector(
        "table#compliant_hearing"
    ).get_attribute("innerHTML")
    time.sleep(random.uniform(1, 3))
    driver.close()
    process_table(table_text=table)


def main(url, city, headless):
    global district_name
    driver = get_driver(headless)
    driver.get(url)
    actions(driver, city)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--district_name", help="Enter district name")
    parser.add_argument(
        "--headless", help="0: run in headful mode, 1: run in headless mode"
    )
    url = "https://haryanarera.gov.in/assistancecontrol/project_search_public/2"
    args = parser.parse_args()
    district_name = args.district_name
    is_headless = args.headless
    headless_opt = {"0": True, "1": False}
    logging.info(f"Entered district: {district_name}")
    main(url=url, city=district_name, headless=headless_opt[is_headless])

# below sample command line to run the script
# python haryanareragovin.py --district_name=GURUGRAM --headless=1
# python haryanareragovin.py --district_name=HISAR --headless=1
