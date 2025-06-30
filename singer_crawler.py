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

# Extract field names from SingerProfile dataclass for data filtering
target_keys = [key.name for key in fields(SingerProfile)]

POPULAR_SINGER_NUM = 20
NORMAL_SINGER_NUM = 10
PAGE_MAX = 3
SINGER_NUM = 60

def get_singer_detail(
    id: int,
    name: str,
    page: int,
    song_num: int
    ) -> SingerProfile:
    """
    Scrape singer details from Kuwo Music
    using Selenium web automation.
    
    This function extracts detailed information about a specific singer 
    including their profile data and song list,
    and returns a structured SingerProfile object.
    
    Args:
        id (int): Target id of the singer
        name (str): Target name of the singer
        page (int): Target page number on the singers listing
                    (1-based indexing)
        song_num (int): Maximum number of songs
                        to retrieve from the singer's catalog
                        
    Returns:
        SingerProfile: Complete singer profile
                       containing biographical information
                       and a curated list of their songs
    """
    
    # Navigate to the specified page number
    path = f'//li[@data-v-9fcc0c74][./span[text()="{page}"]]'
    page_botton = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, path))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", page_botton)
    time.sleep(0.5)
    WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, path))
            ).click()
    time.sleep(1)
    
    # Clean former requests
    if hasattr(driver, 'requests'):
        del driver.requests
    
    # Navigate to the singer's detailed profile page
    artist_button_xpath = f'//span[text()="{name}"]'
    artist_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, artist_button_xpath))
    )
    
    driver.execute_script("arguments[0].scrollIntoView(true);", artist_button)
    time.sleep(0.5)

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, artist_button_xpath))
    ).click()
    time.sleep(1)
    
    # Define API endpoints for detailed singer information
    artist_info_substring = (
        "kuwo.cn/api/www/artist/artist?artistid=" 
        + str(id)
        + '&'
    )
    music_info_substring = (
        "kuwo.cn/api/www/artist/artistMusic?artistid=" 
        + str(id)
        +'&'
    )
    
    # Initialize dict to store the singer's songs
    song_dict = dict()
    
    # Extract song list from music API response
    for request in driver.requests:
        if music_info_substring in request.url:
            with gzip.open(io.BytesIO(request.response.body), 'rb') as f:
                decompressed_data = f.read().decode('utf-8')
                datalist = json.loads(decompressed_data)['data']['list']
                
                # Collect song names from the API response
                for i, songdata in enumerate(datalist):
                    if i < song_num:
                        song_dict[songdata['rid']] = songdata['name']
    
    # Process detailed artist information and create SingerProfile object
    for request in driver.requests:
        if artist_info_substring in request.url:
            with gzip.open(io.BytesIO(request.response.body), 'rb') as f:
                decompressed_data = f.read().decode('utf-8')
                data = json.loads(decompressed_data)['data']
                
                # Check whether the singer is needed
                if data['id'] != id:
                    raise TimeoutError
                
                # Clean up HTML entities in the biographical information
                info = data['info'].replace('&nbsp;', ' ')
                data['info'] = info
                aartist = data['aartist'].replace('&nbsp;', ' ')
                data['aartist'] = aartist
                
                # Filter data to include only fields defined
                # in SingerProfile dataclass
                filtered_data = {
                    key: value
                    for key, value in data.items() 
                    if key in target_keys
                }
                
                filtered_data['song_dict'] = song_dict
                
                # Add orignal url of the singer
                filtered_data['original_url'] = (
                    'https://www.kuwo.cn/singer_detail/'
                    + str(id)
                )
                
                # Modify names
                filtered_data['gender'] = data['gener']
                filtered_data['height'] = data['tall']
                filtered_data['region'] = data['country']
                
                # Create and return the complete singer profile object
                singer_profile = SingerProfile(**filtered_data)
                
                driver.back()
                time.sleep(1)
                return singer_profile
    
    raise TimeoutError

def get_page_detail(page: int) -> dict[int: str]:
    """
    Navigates to a specific singer list page and extracts singer IDs and names.

    Args:
        page (int): The target page number to navigate to.

    Returns:
        dict[int: str]: A dictionary mapping singer IDs to their names.
    """
    # Clean former requests
    if hasattr(driver, 'requests'):
        del driver.requests
    
    # Navigate to the specified page number
    if page != 1:
        path = f'//li[@data-v-9fcc0c74][./span[text()="{page}"]]'
        WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, path))
            ).click()
        
    else:
        # Workaround for page 1: navigate to page 2 first, then back to page 1
        # This is necessary
        # because direct navigation to page 1 doesn't trigger
        # the required API requests for data retrieval
        path = '//li[@data-v-9fcc0c74][./span[text()="2"]]'
        WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, path))
            ).click()
        path = '//li[@data-v-9fcc0c74][./span[text()="1"]]'
        WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, path))
            ).click()
    
    time.sleep(1)    
    
    # Intercept and process API responses to extract singer information
    api_substring = "wapi.kuwo.cn/api/www/artist/artistInfo"
    
    singer_dict = dict()
    
    # Parse intercepted network requests to find singer list data
    for request in driver.requests:
        if api_substring in request.url:
            # Decompress gzip-encoded response data
            singer_dict.clear()
            with gzip.open(io.BytesIO(request.response.body), 'rb') as f:
                decompressed_data = f.read().decode('utf-8')
                data = json.loads(decompressed_data)['data']['artistList']
                
                # Extract basic profile information for the target singer
                # Note: This provides only preliminary data;
                #       detailed info requires additional API calls
                for profile in data:
                    singer_dict[profile['id']] = profile['name']
                  
    return singer_dict
    

def start_crawler(start_page: int = 1, start_place: int = 0):
    
    """
    Initiates the web crawling process, iterating through pages and singers
    to fetch detailed information. The program will terminate immediately
    if any singer's data retrieval fails.

    Args:
        start_page (int): The page number to begin crawling from (1-based).
        start_place (int): The position of the singer on the starting page
                           to begin crawling from (0-based).
    """

    for page in range(start_page, PAGE_MAX + 1):
        
        singer_dict = get_page_detail(page = page)
        count = 0
        
        for id, name in singer_dict.items():
            
            if count < start_place:
                count += 1
                continue
            
            song_num = 0
            if page == 1:
                song_num = POPULAR_SINGER_NUM
            else:
                song_num = NORMAL_SINGER_NUM
        
            singer_profile = get_singer_detail(
                id = id,
                name = name,
                page = page,
                song_num = song_num
            )
            
            if singer_profile.id != -1:
                singer_profile.save_to_local()
                singer_profile.save_picture()

                print("page =", page, "place =", count, "successfully saved")
                count += 1
                
            else:
                # If the crawler failed to get right informaiton
                raise RuntimeError
        start_place = 0

if __name__  == '__main__':
    
    # Configure Chrome browser options for headless scraping
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    )
    
    # Initialize WebDriver and navigate to the singers page
    driver = webdriver.Chrome()
    driver.get("https://www.kuwo.cn/singers")
    time.sleep(1)
    
    start_page = int(input())
    start_place = int(input())
    start_crawler(start_page, start_place)
    driver.quit()