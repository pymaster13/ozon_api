import requests
import json
import logging, time, os, datetime

from bs4 import BeautifulSoup
from django.http import JsonResponse
from fake_useragent import UserAgent
from logging import config, Formatter, getLogger
from logging.handlers import RotatingFileHandler
from selenium import webdriver
from selenium.webdriver import Firefox, Chrome, ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from rest_framework.views import APIView
from rest_framework.response import Response

from .data import api_text
from .models import Product
from .serializers import ProductSerializer

def create_logger():
    logger = logging.getLogger('OZON_api')
    log_file = 'ozon_api.log'
    log_formatter = logging.Formatter('%(asctime)s %(name)s - %(levelname)s:%(message)s')
    handler = RotatingFileHandler(log_file, mode='a', maxBytes=1*1024*1024, backupCount=60)
    handler.setFormatter(log_formatter)
    logger.addHandler(handler)

    return logger

def open_browser():
    profile = webdriver.FirefoxProfile()
    """
    ПОМЕНЯТЬ ПУТЬ К РАСШИРЕНИЮ
    """
    #profile.add_extension(extension='/usr/ozon/ozon_api/doz4@hotmail.com.xpi')
    #profile.install_addon('/root/.mozilla/extensions/doz4@hotmail.com.xpi', temporary=True)    

    cap = DesiredCapabilities.FIREFOX
    cap['marionette'] = True

    options = Options()
    options.headless = True
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")

    """
    ПОМЕНЯТЬ ПУТЬ К ДРАЙВЕРУ
    """
    browser = Firefox(executable_path='/usr/ozon/ozon_api/driver', service_log_path=os.path.devnull, options=options, firefox_profile=profile, capabilities=cap)
    # browser = Firefox(executable_path='/home/element/Projects/ozon_api/ozon_api/driver', service_log_path=os.path.devnull, options=options, firefox_profile=profile, capabilities=cap)
    browser.install_addon('/root/.mozilla/extensions/doz4@hotmail.com.xpi', temporary=True)
    # browser.install_addon('/home/element/Projects/ozon_api/ozon_api/doz4@hotmail.com.xpi', temporary=True)

    browser.maximize_window()        
    time.sleep(1)
    browser.get('about:addons')
    time.sleep(1)
    browser.find_element_by_xpath("//button[@title='Extensions']").click()
    time.sleep(2)
    browser.find_element_by_xpath("//div[@class='addon-name-container']").click()
    time.sleep(2)

    prefs = browser.find_element_by_xpath("//button[@class='tab-button'][text()='Preferences']")
 
    prefs.click()
    time.sleep(0.5)
    prefs.send_keys(Keys.TAB)
    time.sleep(0.5)
    prefs.send_keys(Keys.TAB)
    time.sleep(0.5)
    prefs.send_keys(Keys.TAB)
    time.sleep(0.5)
    prefs.send_keys(Keys.TAB)

    opts = browser.find_element_by_id('addon-inline-options')
    opts.send_keys(Keys.TAB)
    opts.send_keys('************************')
    opts.send_keys(Keys.TAB)
    opts.send_keys(Keys.TAB)
    opts.send_keys(Keys.TAB)
    opts.send_keys(Keys.SPACE)
    opts.send_keys(Keys.TAB)
    opts.send_keys(Keys.SPACE)
    opts.send_keys(Keys.TAB)
    opts.send_keys("1")
    opts.send_keys(Keys.TAB)
    opts.send_keys(Keys.SPACE)
    return browser

class GetProducts(APIView):
    def get(self, request):
        products = Product.objects.all().order_by('id_product')
        serializer = ProductSerializer(products, many=True)
        context = serializer.data
        return JsonResponse(context, safe=False)
