import time
import sys
import argparse
import json
import requests
import ocrspace
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_driver(head = True):
    '''
        return: web driver
    '''
    options = webdriver.ChromeOptions()
    options.headless = head
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument("--disable-notifications")
    try:
        return webdriver.Chrome(executable_path="C:/chromedriver.exe", options=options)
    except:
        return webdriver.Chrome(executable_path='./chromedriver', options=options)

def solve_captcha(api, path):
    '''
        return: captcha answer from OCR Space API
    '''
    try:
        answer = ''.join((api.ocr_file(path) or '').strip().split())
        if answer:
            print('captcha: ', answer)
            return answer
    except Exception as e:
        print(e)
        return False

def parse_table(table, ofile):
    '''
        Parse RegistrationGrid and store it to csv
    '''
    table_soup = BeautifulSoup(table, features="lxml")
    columns = [th.get_text() for th in table_soup.find_all('th')]
    data = []
    for tr in table_soup.select('tbody > tr')[1:]:
        row = tuple(td.get_text().strip() for td in tr.find_all('td'))
        data.append(row)
    try:
        pd.DataFrame(data, columns=columns).to_csv(ofile, index=None)
        time.sleep(20)
        sys.exit(f'Saved data in {ofile}')
    except Exception as e:
        print(e)
        sys.exit(f'Exiting. Something went wrong while writing data to {ofile}')

def submit(driver, api, ofile, scounter=0):
    '''
        Submit the form
    '''
    main_window = driver.current_window_handle
    captcha_png_path = 'captcha.png'
    driver.find_element_by_id('imgCaptcha1').screenshot(captcha_png_path)
    txtbox = driver.find_element_by_id('TextBox1')
    captcha = solve_captcha(api, captcha_png_path)
    if captcha:
        txtbox.clear()
        txtbox.send_keys(captcha)
        time.sleep(2) 
        driver.find_element_by_id("btnSearchDoc").click()
    elif scounter <= 3:
        driver.find_element_by_id("btnSearchDoc").click()
        time.sleep(2)
        scounter += 1
        print(f'Captcha reattempt: {scounter}, Something went wrong')
        submit(driver, api, ofile, scounter)
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table#RegistrationGrid")))
        time.sleep(5)
        driver.switch_to_window(main_window)
        table = driver.find_element_by_id('RegistrationGrid').get_attribute('innerHTML')
        print('Parsing RegistrationGrid')
        parse_table(table, ofile)
    except Exception as e:
        time.sleep(3)
        scounter += 1
        if scounter <= 3 and 'incorrect' in driver.find_element_by_id('Label13').text:
            print(f'Captcha reattempt: {scounter}, Something went wrong')
            submit(driver, api, ofile, scounter)
        else:
            print('Exiting!')

def fill_form(driver, city_val, sro_val, year, doc_no, api):
    '''
        Fill the document form
    '''
    driver.find_element_by_css_selector("input[type='radio'][value='3']").click()
    time.sleep(3)

    get_cities = driver.find_element_by_xpath("//select[@id='ddldistrictfordoc']")
    district_names = [dist.text.strip() for dist in get_cities.find_elements_by_tag_name("option")[1:]]
    with open('districts.json', 'w') as dist_file:
        json.dump({'districts': district_names}, dist_file, indent=4, ensure_ascii=False)

    for city_option in get_cities.find_elements_by_tag_name("option")[1:]:
        if city_val in city_option.text:
            city_option.click()
            print('select city: ', city_option.text)
            break

    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "select#ddlSROName > option:nth-child(2)")))
    time.sleep(1)

    get_sros = driver.find_element_by_xpath("//select[@id='ddlSROName']")
    sro_names = [sr.text.strip() for sr in get_sros.find_elements_by_tag_name("option")[1:]]
    with open(f'sro_json/{city_val}_sros.json', 'w') as sro_file:
        json.dump({'sros': sro_names}, sro_file, indent=4, ensure_ascii=False)

    print(f'SRO for {city_val} \n', sro_names)
    for sro_option in get_sros.find_elements_by_tag_name("option")[1:]:
        if sro_val in sro_option.text:
            sro_option.click()
            print('select sro: ', sro_option.text)
            break
    time.sleep(1)

    get_years = driver.find_element_by_xpath("//select[@id='ddlYearForDoc']")
    for year_option in get_years.find_elements_by_tag_name("option")[1:]:
        if year in year_option.get_attribute('value'):
            year_option.click()
            print('select year: ', year_option.text)
            break
    time.sleep(1)

    txtdocno = driver.find_element_by_id("txtDocumentNo")
    txtdocno.clear()
    txtdocno.send_keys(doc_no)
    time.sleep(1)
    submit(driver, api, f'output/{city_val}_{sro_val}_data.csv')

def actions(driver, city_val, sro_val, year, doc_no, api):
    '''
        Trigger actions
    '''
    driver.find_element_by_css_selector('a.btnclose.btn.btn-danger').click()
    time.sleep(2)
    driver.find_element_by_xpath("//td[@id='mnuSearchTypen1']").click()
    time.sleep(3)
    fill_form(driver, city_val, sro_val, year, doc_no, api)   


def main(url, city, sro, year, doc, api, is_headless=False):
    driver = get_driver(is_headless)
    driver.get(url)
    actions(driver, city, sro, year, doc, api)

parser=argparse.ArgumentParser()
parser.add_argument('--district_name', help='Enter district value')
parser.add_argument('--sro_name', help='Enter sro value')
parser.add_argument('--year', help='Enter year')
parser.add_argument('--doc_no', help='Enter doc no')

url=None

args = parser.parse_args()
district_name = args.district_name
sro_name = args.sro_name
year = args.year
doc_no = args.doc_no

# OCR Space api key
ocrspace_key = ''
ocrspace_api = ocrspace.API(ocrspace_key)

print('Entered args: ',args)

if url is not None:
    main(url, district_name, sro_name, year, doc_no, ocrspace_api)
else:
    print('real url is removed. this script is meant for the reference')

# real url is removed. this script meant for reference
# below sample command line to run the script
# python indexscraper.py --district_name=सातारा  --sro_name='Karad 2' --year=2021 --doc_no=1
# python indexscraper.py --district_name=कोल्हापूर  --sro_name=Chandgad --year=2021 --doc_no=1