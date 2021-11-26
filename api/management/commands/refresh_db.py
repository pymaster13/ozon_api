import requests, time, json

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from selenium.webdriver.common.action_chains import ActionChains

from api.views import create_logger, open_browser
from api.models import Product

class Command(BaseCommand):
    help = 'Refresh database'

    def handle(self, *args, **options):
        start = time.time()
        logger = create_logger()
        logger.warning("Start of refreshing data")

        api_response = requests.get('https://www.dambul-shop.ru/wp-json/my_api/v1/get_ozon_goods')
        api_json = json.loads(api_response.text)

        browser = open_browser()
        for key, good_from_api in api_json.items():
            try:   
                product, created = Product.objects.get_or_create(id_product=good_from_api['goods_id'])
                good_zacup = good_from_api.get('zacup', None)     
                good_link = good_from_api.get('link', None)
                good_price = good_from_api.get('price', 0)
                good_percent_ozon = good_from_api.get('percent_ozon', None)

                if good_zacup == None or good_percent_ozon == None or good_price == 0:
                    product.available = False
                    product.new_price = 0.0
                    product.note = 'One field is null' 
                    product.save()
                    continue

                if good_link == None or 'ТЕСТ' in good_link:
                    product.available = True
                    product.new_price = float(good_price)
                    product.note = 'Incorrect link'
                    product.save()
                    print(product.new_price)                    
                    continue

                browser.get(good_link)
    
                time.sleep(0.5)

                page = BeautifulSoup(browser.page_source, 'lxml')
                captcha = page.find('iframe')
                if captcha:
                    if 'Request unsuccessful.' in captcha.text:
                        logger.warning('Captcha')
                        time.sleep(60)

                page = BeautifulSoup(browser.page_source, 'lxml')

                # Конкретный продукт
                if '/product/' in good_link or '/context/' in good_link:       
                    h2 = page.find_all('h2')
                    sold_out = False
                    not_exist = False
                    for header in h2:
                        if 'Такой страницы не существует' in header.text:
                            product.available = False
                            product.new_price = 0.0
                            product.note = "Page doesn't exist"
                            product.save()
                            not_exist = True
                            break

                        if 'Этот товар закончился' in header.text:
                            sold_out_price = page.find('span', class_='c2h5 c2h7').text
                            sold_out_price = sold_out_price[:-2]
                            sold_out_price_float = ''
                            for digit in sold_out_price:
                                if digit.isdigit():
                                    sold_out_price_float += digit
                                
                            sold_out_price_float = float(sold_out_price_float) - 1

                            calculated_price = (sold_out_price_float*(1-float(good_percent_ozon)*0.01)-100)*0.93

                            if calculated_price < float(good_zacup):
                                sold_out_price_float = None

                            sold_out = True
                        
                    if not_exist:
                        continue

                    # Кнопка Еще ...
                    also_button = browser.find_elements_by_xpath("//div[contains(text(), 'Еще ')]")
                    
                    if also_button:
                        for i in range(5):
                            try:
                                time.sleep(0.5)
                                ActionChains(browser).move_to_element(also_button[0]).click(also_button[0]).perform()   
                                logger.warning('Нажимаем на кнопку ЕЩЕ')
                                break   

                            except:
                                browser.execute_script("window.scrollTo(0, 1300);")

                    page = BeautifulSoup(browser.page_source, 'lxml')

                    captcha = page.find('iframe')
                    if captcha:
                        if 'Request unsuccessful.' in captcha.text:
                            logger.warning('Captcha')
                            time.sleep(60)

                    # Другие предложения от продавцов
                    others = page.findAll('div', attrs={'class':'d4b0'})
                    if others:    
                        all_offers = {}
                        for index, position in enumerate(others):
                            all_offers[index] = {}
                            all_offers[index]['discounted'] = False
                            all_offers[index]['price'] = 0.0
                            all_offers[index]['brand'] = ''
                            all_offers[index]['delivery'] = True

                            for element in position.descendants:
                                try:
                                    name = element.name
                                except:
                                    continue

                                if element.name == 'span' and element.text == 'Уцененный товар':
                                    all_offers[index]['discounted'] = True
                                    continue

                                if element.name == 'div' and 'd4f2' in element.attrs.get('class', ''):
                                    cost = ''
                                    for razr in list(element.text[:-1]):
                                        if razr.isdigit():
                                            cost += razr
                                    cost = float(cost)
                                    all_offers[index]['price'] = cost - 1

                                if element.name == 'div' and 'd4c5' in element.attrs.get('class', '') and 'd4c8' in element.attrs.get('class', ''):
                                    all_offers[index]['brand'] = element.next_element.text

                                if element.name == 'svg':
                                    svg = str(element)
                                    if '00.235.796z' in svg:
                                        all_offers[index]['delivery'] = False
                                        
                        if not sold_out:
                            index = len(all_offers)
                            all_offers[index] = {}
                            all_offers[index]['discounted'] = False
                            all_offers[index]['price'] = 0.0
                            all_offers[index]['brand'] = ''
                            all_offers[index]['delivery'] = True
                            brand = page.find('a', class_='b1c8')
                            if not brand:
                                brand = page.find('span', class_='b1c8')

                            try:
                                if brand.name == 'a':
                                    if 'ozon.ru' in brand['href']:
                                        brand_href = brand['href']
                                    else:
                                        brand_href = 'https://www.ozon.ru' + brand['href']
                                else:
                                    brand_href = ''

                                all_offers[index]['brand'] = brand.text
                            except:
                                pass

                            if page.find('span', class_ ='c2h5'):
                                cost_str = page.find('span', class_ ='c2h5').next_element.text
                                cost = ''
                                for razr in list(cost_str[:-1]):
                                    if razr.isdigit():
                                        cost += razr
                                cost = float(cost)
                                all_offers[index]['price'] = cost - 1

                            discount = page.find('a', text ='Особенности продажи уценённого товара')
                            if discount:
                                all_offers[index]['discounted'] = True
                            else:
                                all_offers[index]['discounted'] = False

                            if 'OZON' not in brand.text:
                                browser.get(brand_href)
                                time.sleep(0.5)
                                seller_page = BeautifulSoup(browser.page_source, 'lxml')
                                captcha = page.find('iframe')
                                if captcha:
                                    if 'Request unsuccessful.' in seller_page.text:
                                        logger.warning('Captcha')
                                        time.sleep(60)
                                seller_delivery = seller_page.find('span', class_='a8d5 a8d7')
                                if seller_delivery:    
                                    if 'рубеж' in seller_delivery.text:
                                        all_offers[index]['delivery'] = False
                                    else:
                                        all_offers[index]['delivery'] = True                        

                        sorted_all_offers = {k: v for k, v in sorted(all_offers.items(), key=lambda item: item[1]['price'])}

                        flag_minimal_price = False
                        flag_second_minimal_price = False
                        flag_dambul = False


                        for key, value in sorted_all_offers.items():
                            if value['discounted'] == True:
                                continue
                            if not value['brand']:
                                continue
                            if value['brand'] == 'Dambul-shop':
                                continue
                            if not value['price']:
                                continue
                            if value['delivery'] == False:
                                continue
                            
                            calculated_price = (value['price']*(1-float(good_percent_ozon)*0.01)-100)*0.93

                            if calculated_price >= float(good_zacup):
                                product.available = True
                                product.new_price = float(value['price'])
                                product.note = ''
                                flag_minimal_price = True
                                break
                            else:
                                continue
                        
                        if not flag_minimal_price:  
                            for key, value in sorted_all_offers.items():
                                if value['discounted'] == True:
                                    continue
                                if not value['brand']:
                                    continue
                                if value['brand'] == 'Dambul-shop':
                                    continue
                                if not value['price']:
                                    continue
                                
                                calculated_price = (value['price']*(1-float(good_percent_ozon)*0.01)-100)*0.93

                                if calculated_price >= float(good_zacup):
                                    product.available = True
                                    product.new_price = float(value['price'])
                                    product.note = 'Product with international delivery'
                                    flag_second_minimal_price = True
                                    break
                                else:
                                    continue

                            if not flag_second_minimal_price:  
                                flag_third = False
                                for key, value in sorted_all_offers.items():  
                                    if value['brand'] == 'Dambul-shop':
                                        continue
                                    else:    
                                        flag_third = True                          
                                        product.available = False    
                                        product.new_price = float(value['price'])
                                        product.note = 'Minimal price does not founded'
                                        break
                                if not flag_third:
                                    product.available = True    
                                    product.new_price = float(good_price)
                                    product.note = 'Dambul is only shop for this product'

                        product.save()

                    else:
                        if sold_out:
                            product.available = True       
                            if sold_out_price_float:
                                product.new_price = sold_out_price_float
                            else:
                                product.new_price = float(good_price)
                            product.note = 'Product is sold out'
                            product.save()
                            continue

                        brand = page.find('a', class_='b1c8')
                        if not brand:
                            brand = page.find('span', class_='b1c8')

                        try:
                            if brand.name == 'a':
                                if 'ozon.ru' in brand['href']:
                                    brand_href = brand['href']
                                else:
                                    brand_href = 'https://www.ozon.ru' + brand['href']
                            else:
                                brand_href = ''
                        except:
                            pass
                        
                        discount = page.find('a', text ='Особенности продажи уценённого товара')
                        if discount:
                            product.available = True                        
                            product.new_price = float(good_price)
                            product.note = 'Product is discounted'
                            product.save()
                            continue

                        if page.find('span', class_ ='c2h5'):
                            cost_str = page.find('span', class_ ='c2h5').next_element.text
                            cost = ''
                            for razr in list(cost_str[:-1]):
                                if razr.isdigit():
                                    cost += razr
                            if not cost:
                                continue
                            cost = float(cost) - 1
                            
                            calculated_price = (cost*(1-float(good_percent_ozon)*0.01)-100)*0.93

                        if brand.text == 'Dambul-shop':
                            product.available = True                   
                            product.new_price = float(cost) + 1
                            product.note = 'Dambul-shop has minimal price'
                            product.save()
                            continue

                        if brand_href:
                            browser.get(brand_href)
                            time.sleep(0.5)
                            seller_page = BeautifulSoup(browser.page_source, 'lxml')
                            captcha = page.find('iframe')
                            if captcha:
                                if 'Request unsuccessful.' in captcha.text:
                                    logger.warning('Captcha')
                                    time.sleep(60)

                            seller_delivery = seller_page.find('span', class_='a8d5 a8d7')
                            if seller_delivery and 'рубеж' in seller_delivery.text:
                                product.available = True                        
                                product.new_price = float(good_price)
                                product.note = 'Product is from China'
                                product.save()
                                continue

                        if calculated_price >= float(good_zacup):
                            product.available = True
                            product.new_price = float(cost)
                            product.note = ''
                        else:
                            product.available = False
                            product.new_price = float(cost)
                            product.note = 'Calculated price < zacup price'

                        product.save()

                elif '/search/' in good_link or '/category/' in good_link:
                    results = page.find('div', class_='b6r7')
                    if results:
                        if 'По вашему запросу товаров сейчас нет' in results.text or 'Простите' in results.text: 
                            product.available = True
                            product.new_price = float(good_price)
                            product.one_field_null = False
                            product.note = 'Search has no results'
                            product.save()
                            continue
                        else:
                            res = results.text.split('найден')[-1].split('товар')[0]
                            res = res[1:]
                            res = res.strip()
                            if int(res) > 24:   
                                browser.find_element_by_name('filter').click()
                                browser.implicitly_wait(1)
                                cheapest = browser.find_elements_by_xpath("//span[text()='Сначала дешевые']")
                                if cheapest:
                                    ActionChains(browser).move_to_element(browser.find_element_by_xpath("//span[text()='Сначала дешевые']")).click(browser.find_element_by_xpath("//span[text()='Сначала дешевые']")).perform()                  
                                    time.sleep(5)     
                    else:
                        product.available = True
                        product.new_price = float(good_price)
                        product.note = 'Search has no results'
                        product.save()
                        continue

                    div_results = page.find('div', class_='widget-search-result-container ao3')
                    all_positions_cats = div_results.findAll('div', attrs={"class": "a0t8 a0u"})
                    if all_positions_cats:
                        all_positions = all_positions_cats
                    else:
                        all_positions = div_results.findAll('div', attrs={"class": "a0s9"})
                    all_offers = {}
                    for index, position in enumerate(all_positions):
                        all_offers[index] = {}
                        all_offers[index]['discounted'] = False
                        all_offers[index]['price'] = float(good_zacup)
                        all_offers[index]['brand'] = ''
                        all_offers[index]['delivery'] = True

                        for element in position.descendants:

                            try:
                                name = element.name
                            except:
                                continue

                            if element.name == 'span' and element.text == 'Уцененный товар':
                                all_offers[index]['discounted'] = True

                            if element.name == 'span' and 'b5v6' in element.get('class', '') and 'b5v7' in element.get('class', ''):
                                cost = ''
                                for razr in list(element.text[:-1]):
                                    if razr.isdigit():
                                        cost += razr
                                cost = float(cost)
                                all_offers[index]['price'] = cost - 1

                            if element.name == 'span' and 'f-tsBodyM' in element.get('class', '') and 'Продавец' in element.text:
                                all_offers[index]['brand'] = element.text.replace('Продавец ', '')

                            if element.name == 'span' and 'a8d5' in element.get('class', '') and 'a8d7' in element.get('class', '') :
                                if 'рубеж' in element.text:
                                    all_offers[index]['delivery'] = False
                                else:
                                    all_offers[index]['delivery'] = True
                    
                    sorted_all_offers = {k: v for k, v in sorted(all_offers.items(), key=lambda item: item[1]['price'])} 

                    flag_minimal_price = False
                    flag_second_minimal_price = False
                    
                    for key, value in sorted_all_offers.items():
                        if value['discounted'] == True:
                            continue
                        if not value['brand']:
                            continue
                        if value['brand'] == 'Dambul-shop':
                            continue
                        if not value['price']:
                            continue
                        if value['delivery'] == False:
                            continue

                        calculated_price = (value['price']*(1-float(good_percent_ozon)*0.01)-100)*0.93

                        if calculated_price >= float(good_zacup):
                            flag_minimal_price = True
                            product.available = True
                            product.new_price = float(value['price'])
                            product.note = ''
                            break
                        else:
                            continue
                    
                    if not flag_minimal_price:
                        for key, value in sorted_all_offers.items():
                            if value['discounted'] == True:
                                continue
                            if not value['brand']:
                                continue
                            if value['brand'] == 'Dambul-shop':
                                continue
                            if not value['price']:
                                continue

                            calculated_price = (value['price']*(1-float(good_percent_ozon)*0.01)-100)*0.93

                            if calculated_price >= float(good_zacup):
                                product.available = True
                                product.new_price = float(value['price'])
                                product.note = 'Product with international delivery'
                                flag_second_minimal_price = True
                                break
                            else:
                                continue

                        if not flag_second_minimal_price:  
                            flag_third = False
                            for key, value in sorted_all_offers.items():  
                                if value['brand'] == 'Dambul-shop':
                                    continue
                                else:    
                                    flag_third = True                          
                                    product.available = False    
                                    product.new_price = float(value['price'])
                                    product.note = 'Minimal price does not founded'
                                    break
                            if not flag_third:
                                product.available = True    
                                product.new_price = float(good_price)
                                product.note = 'Dambul is only shop for this product'

                    product.save()

            except Exception as e:
                logger.error(e)
                continue

        work_time = time.time() - start
        logger.warning('Script worked {} secs'.format(work_time))
        logger.handlers.pop()
        browser.quit()


