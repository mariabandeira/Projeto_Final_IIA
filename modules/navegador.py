from selenium import webdriver
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from bs4 import BeautifulSoup

class Navegador:
    def __init__ (self):
        self.options = FirefoxOptions()
        self.options.add_argument("--headless")
        #self.options.add_argument("--width=600")
        #self.options.add_argument("--height=800")
        self.service = Service('/snap/bin/firefox.geckodriver')
        self.driver = webdriver.Firefox(service=self.service, options=self.options)
        self.stars_count = 0
        self.reviews_count = 0
        self.current_url = None
        
        script = """
        navigator.geolocation.getCurrentPosition = function(success){
            var position = {"coords" : {"latitude": "34.0207305","longitude": "-118.6919153"}};
            success(position);
        }
        """
        self.driver.execute_script(script)

    def get_url(self, productID):
        self.productID = productID
        self.driver.get(f'https://www.amazon.com/dp/{productID}/')
        self.current_url = self.driver.current_url
        
        #make this using beautifulsoup
        try:
            see_all_reviews = self.driver.find_element(By.XPATH, '//a[@data-hook="see-all-reviews-link-foot"]')
            self.driver.execute_script("arguments[0].scrollIntoView();", see_all_reviews)
            self.driver.execute_script("window.scrollBy(0, -150)")
            self.more_reviews_href = see_all_reviews.get_attribute('href')
        except Exception as e:
            print(e)
    
    def _goto_url(self):
        self.driver.get(self.more_reviews_href)
    
    def get_first_review(self):
        if self.driver.current_url != self.more_reviews_href:
            self.driver.get(self.more_reviews_href)
        first_review = self.driver.find_element(By.XPATH, '//div[starts-with(@id, "customer_review-")]')
        
        return first_review
    
    def get_first_page_reviews(self):
        if self.driver.current_url != self.more_reviews_href:
            self.driver.get(self.more_reviews_href)

        reviews = self.driver.find_elements(By.XPATH, '//div[starts-with(@id, "customer_review-")]')
        reviews_soups = [BeautifulSoup(review.get_attribute('outerHTML'), 'html.parser') for review in reviews]

        spans_all = [review_soup.find_all('span') for review_soup in reviews_soups]
        #spans_all = [[span.text for span in spans] for spans in spans_all]
        #spans_all = [[stext for stext in spans if stext.text != ''] for spans in spans_all]

        models = [review_soup.find_all('a', {'data-hook': 'format-strip'}) for review_soup in reviews_soups]
        #models = [[model.text for model in models_list] for models_list in models]

        #info = []
        #for i in range(len(reviews_soups)):
        #    spans_all[i].append(models[i][0])
        #    info.append(spans_all[i])

        return spans_all, models

    def get_stars_resume(self):
        if self.driver.current_url != self.more_reviews_href:
            self.driver.get(self.more_reviews_href)
            
        stars = {}
        
        for i in range(1, 6):
            try:
                star = self.driver.find_element(By.XPATH, f'//tr[starts-with(@aria-label, "{i} stars")]')
                stars[i] = star.text.split('\n')[1]
            except NoSuchElementException:
                stars[i] = 0    
        return stars
    
    def get_reviews_location(self):
        if self.driver.current_url != self.more_reviews_href:
            self.driver.get(self.more_reviews_href)
        reviews_location = self.driver.find_element(By.XPATH, '//h3[@data-hook="arp-local-reviews-header"]')
        return reviews_location.text

    def get_review_count(self):
        if self.driver.current_url != self.more_reviews_href:
            self.driver.get(self.more_reviews_href)
        # encontra sequências de números seguidos por um espaço
        # disabled for now
        # pattern = r'\d{1,3}(,\d{3})*(?=\s)'
        # reviews_stars = re.findall(pattern, review_count_text)
        # reviews_stars = [int(review.replace(',', '')) for review in reviews_stars if review != '']

        review_count = self.driver.find_element(By.XPATH, '//div[@data-hook="cr-filter-info-review-rating-count"]')
        review_count_text = review_count.text

        # ATS
        _split = review_count_text.split(' ')
        stars_count = _split[0]
        for i in range(len(_split)):
            if _split[i] == 'ratings,':
                reviews_count = _split[i+1]
                break

        try:
            stars_count = stars_count.replace(',', '')
            reviews_count = reviews_count.replace(',', '')
        except Exception as e:
            print(e)
        try:
            stars_count = int(stars_count)
            reviews_count = int(reviews_count)
        except Exception as e:
            print(e)

        # número total de reviews
        self.stars_count = stars_count
        self.reviews_count = reviews_count
        return self.stars_count, self.reviews_count 
    
    def set_dropdown(self, dropdown_type, dropdown_option):
        if self.driver.current_url != self.more_reviews_href:
            self.driver.get(self.more_reviews_href)

        self.driver.execute_script("window.scrollBy(0, 150)")

        dropdown_filters = self.driver.find_elements(By.XPATH, '//span[@data-csa-c-func-deps="aui-da-a-dropdown-button"]')
        dropdown = None

        for _filter in dropdown_filters:
            if _filter.text == dropdown_type:
                dropdown = _filter
                break

        if dropdown is not None:
            dropdown.click()
            dropdown_options = self.driver.find_elements(By.XPATH, '//li[starts-with(@class, "a-dropdown-item")]')
            for option in dropdown_options:
                if option.text == dropdown_option:
                    option.click()
                    self.more_reviews_href = self.driver.current_url
                    self.current_url = self.driver.current_url
                    break
        else:
            print('Dropdown não encontrado.')

    def get_reviews(self):
        all_infos = []
        delta_y = 10000
        #page = 0
        while True:
            try:
                #page += 1
                #print(f'Página {page}')
                self.driver.execute_script(f"window.scrollBy(0, {delta_y})")
                WebDriverWait(self.driver, 2).until(EC.invisibility_of_element_located((By.XPATH, '//div[@class="a-section cr-list-loading reviews-loading"]')))
                
                WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.XPATH, '//div[starts-with(@id, "customer_review-")]')))
                
                reviews = self.driver.find_elements(By.XPATH, '//div[starts-with(@id, "customer_review-")]')
                reviews_soups = [BeautifulSoup(review.get_attribute('outerHTML'), 'html.parser') for review in reviews]

                spans_all = [review_soup.find_all('span') for review_soup in reviews_soups]
                spans_all = [[span.text for span in spans] for spans in spans_all]
                spans_all = [[stext for stext in spans if stext != ''] for spans in spans_all]

                models = [review_soup.find_all('a', {'data-hook': 'format-strip'}) for review_soup in reviews_soups]
                models = [[model.text for model in models_list] for models_list in models]

                
                info = []
                for i in range(len(reviews_soups)):
                    spans_all[i].append(models[i][0])
                    info.append(spans_all[i])

                all_infos.append(info)

                next_page = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, '//div[@id="cm_cr-pagination_bar"]//li[@class="a-last"]')))
                self.driver.execute_script("arguments[0].scrollIntoView();", next_page)
                self.driver.execute_script("window.scrollBy(0, -150)")
                
                next_page = self.driver.find_element(By.XPATH, '//div[@id="cm_cr-pagination_bar"]//li[@class="a-last"]')
                next_page.click()
            except Exception as e:
                print(e)
                #print('Não foi possível encontrar mais avaliações.')
                break

        return all_infos
        
    def __del__(self):
        self.driver.quit()
        print('Navegador fechado.')