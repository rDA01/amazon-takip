import asyncio
import logging
import requests
from bs4 import BeautifulSoup
import threading

from data.entities.product import Product
from data.repositories.productRepository import ProductRepository
from service.productService import ProductService
from service.telegramService import TelegramService
import time
import requests
import random

class LoggingConfigurator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        handler = logging.FileHandler('application.log')
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

class GatherPagesItems(LoggingConfigurator):
    def __init__(self, product_repo,url):
        self.base_url = url
        self.header = ({'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'})
        self.page_count=0
        self.item_count=0
        self.product_repo = product_repo

    async def gather_page_number(self, base_url, i):
        
        try:
            time.sleep(random.uniform(1, 5))
            print("----------New Iteration-----------: ",i)
            print(base_url) 
            response = requests.get(base_url + str(i),headers=self.header)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                divs = soup.find_all('div', class_='sg-col-inner')
                print(len(divs))
                for div in divs:
                    h3 = div.find('h2', class_='a-size-mini a-spacing-none a-color-base s-line-clamp-4')
                    
                    a = div.find('a',class_='a-link-normal', href=True)
                    
                    prc_box_dscntd = div.find('span', class_='a-offscreen')
                    
                    
                    if h3 and a and prc_box_dscntd:
                        title = h3.get_text(strip=True)
                        
                        href = a['href']
                        href = href.split("?")[0]
                        item =  self.product_repo.get_product_by_link(href)
                        price_text = prc_box_dscntd.text.strip()
                        price_text = price_text.replace('.', '').replace(',', '.')  # Replace comma with dot
                        price = float(''.join(filter(lambda x: x.isdigit() or x == '.', price_text)))                        
                        
                        if item is False:


                            product = Product(id=None,title=title, link=href, price=price)
                            
                            self.product_repo.add_product(product)
                        else:
                            print("Item exists") 
                                               
            
                    else:
                        
                        print("Incomplete data found in div, skipping.")
                
                div_count = len(divs)
                #if div_count != 24:
                    #self.item_count = (i * 24) + div_count
                    #self.page_count = i
                    #print("False")
                    #return False
            else:
                
                print("Failed to retrieve page:", response.status_code)
                
                
                return False
        except Exception as err:
            print("Error occurred:", err)
            return False
        
        return True

    async def gather_page_numbers(self):
        base_url = self.base_url
        loop_var = True
        i = 1
        response = requests.get(base_url + str(i),headers=self.header)
        soup = BeautifulSoup(response.content, 'html.parser')
        last_page = soup.find('span',class_='s-pagination-item s-pagination-disabled')
        last_pageIndex = int(last_page.get_text())
        
        while loop_var and i <= last_pageIndex:
            #threads = []
            #for _ in range(50):
            #    t = threading.Thread(target=self.gather_page_number, args=(base_url, i))
            #    t.start()
            #    threads.append(t)
            #    i += 1
            #for t in threads:
            #    t.join()
            loop_var = await self.gather_page_number(base_url, i)
            i = i + 1

async def Main():
    product_repo = ProductRepository()

    smartphones = GatherPagesItems(product_repo,"https://www.amazon.com.tr/s?i=electronics&rh=n%3A13709907031&dc&fs=true&page=")
    
    await smartphones.gather_page_numbers()

    #dysonproducts = GatherPagesItems(product_repo,"https://www.trendyol.com/dyson-dik-supurge-x-b102989-c109454?pi=")
    #await dysonproducts.gather_page_numbers()
    
    telegram_service = TelegramService(bot_token='7393980187:AAGJHwoW6DY98jZOvTzdq0o7Ojt8X1VO28Q', chat_id='-4259522500')

    productService = ProductService(product_repo, telegram_service)
    
    while True:
        await productService.updateProduct()

asyncio.run(Main())