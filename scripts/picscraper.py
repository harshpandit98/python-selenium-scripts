import pandas as pd
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from parsel import Selector
from selenium.common.exceptions import TimeoutException

driver = webdriver.PhantomJS(service_args=["--load-images=no"])

class PICScraper():
    def __init__(self):
        self.site_url = None
        self.categories = {
            'Capacitance': '/search/product.html?categoryId=1207',
            'Circuit Protection': '/search/product.html?categoryId=1097',
            'Connector': '/search/product.html?categoryId=1102',
            'Radio Frequency': '/search/product.html?categoryId=953',
            'Sensor': '/search/product.html?categoryId=958',
            'Switch/Relay': '/search/product.html?categoryId=1566',
            'Tools/Accessories': '/search/product.html?categoryId=1613'
        }

    def scrape(self):
        if self.site_url is not None:
            for category, category_url in self.categories.items():
                self.select_scrap(self.site_url+category_url, category)
                print(f'\nScrapped {category}'.upper())
        else:
            print('real url is removed. this script is meant for the reference')
        driver.quit()

    def select_scrap(self, url, filename):
        driver.get(url)
        time.sleep(8)
        driver.find_element_by_xpath('//label[input[@id="filter-isInventory-input"]]').click()
        time.sleep(8)
        data = []
        try:
            _ = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'list_totalPages')))
            total_pages = driver.find_element_by_xpath('//*[@id="list_totalPages"]').text
            print(f'Total pages: {total_pages}')
            data = self.paginate(total_pages=int(total_pages))
        
        except TimeoutException as te:
            print('Loading took too much time!')
        
        finally:
            # save file
            if data:
                Path("data").mkdir(parents=True, exist_ok=True)
                
                filename = filename.replace('/','-').replace(' ','-').lower()

                columns = ['MPN', 'Manufacturer', 'Price', 'Inventory', 'Part Url']
                df = pd.DataFrame(data, columns = columns)
                df.to_excel(f'data/{filename}.xlsx', index=False)

    def paginate(self, **kwargs):
        items = []
        start = kwargs.get('start',1)
        # print(start)
        if start > 1:
            driver.find_element_by_xpath("//input[@pagination_inp]").send_keys(start)
            time.sleep(1)
            driver.find_element_by_xpath("//button[@pagination_go]").click()
            time.sleep(5)
        
        try:
            for page_num in range(start, kwargs.get('total_pages',0) + 1):
                print(f'Collecting from page: {page_num}')
                response = Selector(text=driver.page_source)
                
                for tr in response.css('tbody#list_tbody_list > tr'):
                    item = {}
                    part = tr.css('a[class="listPro_code preText"]::text').get()
                    item["MPN"] = part.strip() if part else ''
                    
                    mfr = tr.xpath('.//div[@for-auth]/a/text()').get()
                    item["Manufacturer"] = mfr.strip() if mfr else ''

                    price_tr = tr.css('td[class="text-center js-nr-td"] tbody > tr:last-child')

                    item['Price'] = '{}{}'.format(
                        price_tr.css('td::text').get() or tr.xpath('.//span[@class="text-muted--er"]/text()').get() or '',
                        price_tr.css('td:last-child::text').get() or tr.xpath('.//span[@class="text-muted--er"]/a/text()').get() or ''
                    )

                    item['Inventory'] = '{}{}'.format(
                            tr.css('div[class="listPro_tdCon"] > p::text').get() or '',
                            tr.css('div[class="listPro_tdCon"] > p > span::text').get() or ''
                    )

                    item['Part Url'] = self.site_url + tr.css('a[class="listPro_code preText"]::attr(href)').get()
                    print(item)
                    items.append(item)

                driver.find_element_by_xpath("//span[@id='list_page_next']").click()
                time.sleep(3)
        finally:
            return items

if __name__ == '__main__':
    scraper = PICScraper()
    scraper.scrape()

# real url is removed. this script for reference
# below sample command line to run the script
# to run the script
# python picscraper.py