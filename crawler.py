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

def get_singer_detail(page: int, place: int, songnum: int) -> SingerProfile:
    """
    Scrape singer details from Kuwo Music using Selenium web automation.
    
    This function navigates to the Kuwo Music singers page, extracts detailed
    information about a specific singer including their profile data and song list,
    and returns a structured SingerProfile object.
    
    Args:
        page (int): Target page number on the singers listing (1-based indexing)
        place (int): Position of the singer on the specified page (0-based indexing)
        songnum (int): Maximum number of songs to retrieve from the singer's catalog
        
    Returns:
        SingerProfile: Complete singer profile containing biographical information
                      and a curated list of their songs
    """
    
    # Configure Chrome browser options for headless scraping
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    )
    
    # Initialize WebDriver and navigate to the singers page
    driver = webdriver.Chrome()
    driver.get("https://www.kuwo.cn/singers")
    time.sleep(1)
    
    # Navigate to the specified page number
    if page != 1:
        path = '//li[@data-v-9fcc0c74][./span[text()="' + str(page) + '"]]'
        check_input = driver.find_element(By.XPATH, path)
        check_input.click()
    else:
        # Workaround for page 1: navigate to page 2 first, then back to page 1
        # This is necessary because direct navigation to page 1 doesn't trigger
        # the required API requests for data retrieval
        driver.find_element(By.XPATH, '//li[@data-v-9fcc0c74][./span[text()="2"]]').click()
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
                decompressed_data = f.read()
                data = json.loads(decompressed_data.decode('utf-8'))['data']['artistList']
                
                # Extract basic profile information for the target singer
                # Note: This provides only preliminary data;
                #       detailed info requires additional API calls
                profile = data[place]
                name = profile['name']
                id = profile['id']
    
    # Navigate to the singer's detailed profile page
    artist_button = driver.find_element(By.XPATH, '//span[text()="' + name + '"]')
    artist_button.click()
    time.sleep(1)
    
    # Define API endpoints for detailed singer information
    artist_info_substring = "kuwo.cn/api/www/artist/artist?artistid=" + str(id)
    music_info_substring = "kuwo.cn/api/www/artist/artistMusic?artistid=" + str(id)
    
    # Initialize list to store the singer's songs
    song_list = []
    
    # Extract song list from music API response
    for request in driver.requests:
        if music_info_substring in request.url:
            with gzip.open(io.BytesIO(request.response.body), 'rb') as f:
                decompressed_data = f.read()
                datalist = json.loads(decompressed_data.decode('utf-8'))['data']['list']
                
                # Collect song names from the API response
                for songdata in datalist:
                    song_list.append(songdata['name'])
    
    # Process detailed artist information and create SingerProfile object
    for request in driver.requests:
        if artist_info_substring in request.url:
            with gzip.open(io.BytesIO(request.response.body), 'rb') as f:
                decompressed_data = f.read()
                data = json.loads(decompressed_data.decode('utf-8'))['data']
                
                # Clean up HTML entities in the biographical information
                info = data['info'].replace('&nbsp;', ' ')
                data['info'] = info
                aartist = data['aartist'].replace('&nbsp;', ' ')
                data['aartist'] = aartist
                
                # Filter data to include only fields defined in SingerProfile dataclass
                filtered_data = {
                    key: value
                    for key, value in data.items() 
                    if key in target_keys
                }
                
                # Limit song list to requested number and add to profile data
                filtered_data['song_list'] = song_list[0: songnum]
                
                # Add orignal url of the singer
                filtered_data['orignal_url'] = 'https://www.kuwo.cn/singer_detail/' + str(id)
                
                # Modify names
                filtered_data['gender'] = data['gener']
                filtered_data['height'] = data['tall']
                
                # Create and return the complete singer profile object
                singer_profile = SingerProfile(**filtered_data)
                driver.quit()
                return singer_profile
    
    driver.quit()
    raise TimeoutError

singer_object = get_singer_detail(1, 1, 4)
for key in target_keys:
    print(key, ': ', singer_object.__dict__.get(key))