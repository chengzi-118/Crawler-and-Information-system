import requests
from bs4 import BeautifulSoup
import json
from Singer import SingerProfile
from dataclasses import fields
from selenium.webdriver.common.by import By
from seleniumwire import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import gzip
import io

target_keys = [key.name for key in fields(SingerProfile)]

def complete_singer_detail(page: int, place: int):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    )
    
    driver = webdriver.Chrome()
    driver.get("https://www.kuwo.cn/singers")
    time.sleep(1)
    
    if page != 1:
        path = '//li[@data-v-9fcc0c74][./span[text()="' + str(page) + '"]]'
        check_input = driver.find_element(By.XPATH, path)
        check_input.click()
    else:
        driver.find_element(By.XPATH, '//li[@data-v-9fcc0c74][./span[text()="2"]]').click()
        time.sleep(1)
        driver.find_element(By.XPATH, '//li[@data-v-9fcc0c74][./span[text()="1"]]').click()
    
    time.sleep(1)
    
    target_api_substring = "wapi.kuwo.cn/api/www/artist/artistInfo"
    
    name: str = ''
    id: int = -1
    
    for request in driver.requests:
        if target_api_substring in request.url:
            with gzip.open(io.BytesIO(request.response.body), 'rb') as f:
                decompressed_data = f.read()
                data = json.loads(decompressed_data.decode('utf-8'))['data']['artistList']
                profile = data[place]
                name = profile['name']
                id = profile['id']
    
    artist_button = driver.find_element(By.XPATH, '//span[text()="' + name + '"]')
    artist_button.click()
    time.sleep(1)
    
    target_substring = "kuwo.cn/api/www/artist/artist?artistid=" + str(id)
    for request in driver.requests:
        if target_substring in request.url:
            with gzip.open(io.BytesIO(request.response.body), 'rb') as f:
                decompressed_data = f.read()
                data = json.loads(decompressed_data.decode('utf-8'))['data']
                info = data['info'].replace('&nbsp;', ' ')
                data['info'] = info
                filtered_data = {
                    key: data.get(key, getattr(SingerProfile, key))
                    for key in target_keys
                }
                singer_profile = SingerProfile(**filtered_data)
                singer_profile.info
                return singer_profile

singer_object = complete_singer_detail(1, 0)
print(singer_object.info)