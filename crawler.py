import json
from Singer import SingerProfile
from dataclasses import fields
from selenium.webdriver.common.by import By
from seleniumwire import webdriver
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
    page: int,
    place: int,
    song_num: int
    ) -> SingerProfile:
    """
    Scrape singer details from Kuwo Music
    using Selenium web automation.
    
    This function navigates to the Kuwo Music singers page,
    extracts detailed information about a specific singer 
    including their profile data and song list,
    and returns a structured SingerProfile object.
    
    Args:
        page (int): Target page number on the singers listing
                    (1-based indexing)
        place (int): Position of the singer on the specified page
                     (0-based indexing)
        song_num (int): Maximum number of songs
                        to retrieve from the singer's catalog
                        
    Returns:
        SingerProfile: Complete singer profile
                       containing biographical information
                       and a curated list of their songs
    """
    
    driver.get("https://www.kuwo.cn/singers")
    time.sleep(1)
    
    # Navigate to the specified page number
    if page != 1:
        path = f'//li[@data-v-9fcc0c74][./span[text()="{page}"]]'
        check_input = driver.find_element(By.XPATH, path)
        check_input.click()
    else:
        # Workaround for page 1: navigate to page 2 first, then back to page 1
        # This is necessary
        # because direct navigation to page 1 doesn't trigger
        # the required API requests for data retrieval
        driver.find_element(
            By.XPATH,
            '//li[@data-v-9fcc0c74][./span[text()="2"]]'
        ).click()
        time.sleep(1)
        driver.find_element(By.XPATH, '//li[@data-v-9fcc0c74][./span[text()="1"]]').click()
    
    time.sleep(1)
    
    # Intercept and process API responses to extract singer information
    api_substring = "wapi.kuwo.cn/api/www/artist/artistInfo"
    
    # Initialize variables to store singer identification data
    name: str = ''
    id: int = -1
    
    # Parse intercepted network requests to find singer list data
    for request in driver.requests:
        if api_substring in request.url:
            # Decompress gzip-encoded response data
            with gzip.open(io.BytesIO(request.response.body), 'rb') as f:
                decompressed_data = f.read().decode('utf-8')
                data = json.loads(decompressed_data)['data']['artistList']
                
                # Extract basic profile information for the target singer
                # Note: This provides only preliminary data;
                #       detailed info requires additional API calls
                profile = data[place]
                name = profile['name']
                id = profile['id']
    
    # Navigate to the singer's detailed profile page
    artist_button = driver.find_element(
        By.XPATH,
        '//span[text()="' + name + '"]'
    )
    artist_button.click()
    time.sleep(1)
    
    # Define API endpoints for detailed singer information
    artist_info_substring = (
        "kuwo.cn/api/www/artist/artist?artistid=" 
        + str(id)
    )
    music_info_substring = (
        "kuwo.cn/api/www/artist/artistMusic?artistid=" 
        + str(id)
    )
    
    # Initialize list to store the singer's songs
    song_list = []
    
    # Extract song list from music API response
    for request in driver.requests:
        if music_info_substring in request.url:
            with gzip.open(io.BytesIO(request.response.body), 'rb') as f:
                decompressed_data = f.read().decode('utf-8')
                datalist = json.loads(decompressed_data)['data']['list']
                
                # Collect song names from the API response
                for songdata in datalist:
                    song_list.append(songdata['name'])
    
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
                
                # Limit song list to requested number and add to profile data
                filtered_data['song_list'] = song_list[0: song_num]
                
                # Add orignal url of the singer
                filtered_data['original_url'] = (
                    'https://www.kuwo.cn/singer_detail/'
                    + str(id)
                )
                
                # Modify names
                filtered_data['gender'] = data['gener']
                filtered_data['height'] = data['tall']
                
                # Create and return the complete singer profile object
                singer_profile = SingerProfile(**filtered_data)
                return singer_profile
    
    raise TimeoutError

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
        for place in range(start_place, SINGER_NUM):
            
            song_num = 0
            if page == 1:
                song_num = POPULAR_SINGER_NUM
            else:
                song_num = NORMAL_SINGER_NUM
        
            singer_profile = get_singer_detail(
                page = page,
                place = place,
                song_num = song_num
            )
            
            if singer_profile.id != -1:
                singer_profile.save_to_local()
                singer_profile.save_picture()

                print("page = ", page, "place = ", place, "successfully saved")
                
                # Clean all the requests
                driver.execute_script("window.localStorage.clear();")
                driver.execute_script("window.sessionStorage.clear();")
            else:
                # If the crawler failed to get right informaiton
                raise RuntimeError

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
    
    start_page = int(input())
    start_place = int(input())
    start_crawler(start_page, start_place)
    driver.quit()