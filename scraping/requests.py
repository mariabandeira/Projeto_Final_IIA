from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.create_df import create_df
from modules.create_df import pre_treat
import time

class Navegador:
    def __init__ (self):           
        self.options = FirefoxOptions()
        self.options.add_argument("--headless")
        #self.options.add_argument("--width=600")
        #self.options.add_argument("--height=600")
        self.service = Service('/snap/bin/firefox.geckodriver')
        self.driver = webdriver.Firefox(service=self.service, options=self.options)
    
    def get_reviews_url(self, product_id):
        self.driver.get(f"https://www.amazon.com/dp/{product_id}")
        try:
            self.driver.execute_script(f"window.scrollBy(0, 2000)")
            see_all_reviews = self.driver.find_element(By.XPATH, '//a[@data-hook="see-all-reviews-link-foot"]')
            self.driver.execute_script("arguments[0].scrollIntoView();", see_all_reviews)
            self.driver.execute_script("window.scrollBy(0, -150)")
            self.reviews_href = see_all_reviews.get_attribute('href')
        except Exception as e:
            print(e)
            return None

        self.base_url = self.reviews_href
        #self.driver.get(self.reviews_href)

        self.positive_url = self.base_url + "&filterByStar=positive"
        self.negative_url = self.base_url + "&filterByStar=critical"

        return self.reviews_href
    def get_url(self, url):
        self.driver.get(url)
        return self.driver.page_source
    
    def get_positive_reviews(self):
        print('getting positive reviews...')
        positive_info = []

        index = 0
        while True:
            try:
                index += 1
                current_url = self.positive_url + "&pageNumber=" + str(index)
                self.driver.get(current_url)
                time.sleep(3)

                reviews = self.driver.find_elements(By.XPATH, '//div[starts-with(@id, "customer_review-")]')
                reviews_soups = [BeautifulSoup(review.get_attribute('outerHTML'), 'html.parser') for review in reviews]

                spans_all = [review_soup.find_all('span') for review_soup in reviews_soups]
                spans_all = [[span.text for span in spans] for spans in spans_all]
                spans_all = [[stext for stext in spans if stext != ''] for spans in spans_all]

                #models = [review_soup.find_all('a', {'data-hook': 'format-strip'}) for review_soup in reviews_soups]

                #if len(models[0]) != 0:
                #    models = [[model.text for model in models_list] for models_list in models]
                #    for i in range(len(reviews_soups)):
                #        spans_all[i].append(models[i][0])

                info = []
                for i in range(len(reviews_soups)):
                    info.append(spans_all[i])

                positive_info.append(info)
                
                self.driver.execute_script(f"window.scrollBy(0, 2000)")
                try:
                    self.driver.find_element(By.XPATH, '//li[@class="a-disabled a-last"]')
                    break
                except:
                    pass

                if index == 10:
                    break
            except Exception as e:
                print(e)
                break
        return positive_info

    def get_negative_reviews(self):
        print('getting negative reviews...')
        negative_info = []

        index = 0
        while True:
            try:
                index += 1
                current_url = self.negative_url + "&pageNumber=" + str(index)
                self.driver.get(current_url)
                time.sleep(3)

                reviews = self.driver.find_elements(By.XPATH, '//div[starts-with(@id, "customer_review-")]')
                reviews_soups = [BeautifulSoup(review.get_attribute('outerHTML'), 'html.parser') for review in reviews]

                spans_all = [review_soup.find_all('span') for review_soup in reviews_soups]
                spans_all = [[span.text for span in spans] for spans in spans_all]
                spans_all = [[stext for stext in spans if stext != ''] for spans in spans_all]

                #models = [review_soup.find_all('a', {'data-hook': 'format-strip'}) for review_soup in reviews_soups]
                
                
                #if len(models[0]) != 0:
                #    models = [[model.text for model in models_list] for models_list in models]
                #    for i in range(len(reviews_soups)):
                #        spans_all[i].append(models[i][0])
                
                info = []
                for i in range(len(reviews_soups)):
                    info.append(spans_all[i])

                negative_info.append(info)

                self.driver.execute_script(f"window.scrollBy(0, 2000)")
                try:
                    self.driver.find_element(By.XPATH, '//li[@class="a-disabled a-last"]')
                    break
                except:
                    pass
                
                if index == 10:
                    break
            except Exception as e:
                print(e)
                break

        return negative_info
    
    def __del__(self):
        self.driver.quit()
        self.service.stop()

def export_reviews(id_list):
    '''
    id_list - list of product ids
    exports the negative and positive reviews to a csv file in /datasets
    '''

    navegador = Navegador()
    for product_id in id_list:
        print(f'Product id: {product_id}')
        reviews_url = navegador.get_reviews_url(product_id)
        time.sleep(3)
        if reviews_url is None:
            print('No reviews found')
            continue

        positive_reviews = navegador.get_positive_reviews()
        time.sleep(3)
        negative_reviews = navegador.get_negative_reviews()
        time.sleep(3)

        positive_treated = pre_treat(positive_reviews)
        negative_treated = pre_treat(negative_reviews)

        df_positive = create_df(positive_treated, product_id)
        df_negative = create_df(negative_treated, product_id)

        df_positive.to_csv(f'../datasets/POSITIVE_{product_id}.csv', index=False, sep=';')
        df_negative.to_csv(f'../datasets/NEGATIVE_{product_id}.csv', index=False, sep=';')
    del navegador
    
    return True

if __name__ == '__main__':
    with open('product_ids.txt', 'r') as f:
        product_ids = f.readlines()
    
    export_reviews(product_ids)