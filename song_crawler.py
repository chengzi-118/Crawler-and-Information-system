import json
from Song import SongProfile, CommentProfile
from seleniumwire import webdriver
import selenium.common.exceptions as exceptions
import time
import gzip
import io
import random
import os
import threading

def filter_lyric(
    id: int,
    requests: webdriver.Chrome.requests
) -> str:
    """
    Filter lyric from requests.

    Args:
        id (int): kuwo_id of the song.
        requests (webdriver.Chrome.requests): Requests from
            certain url.
            
    Returns:
        A string of lyric.
    """
    
    
    # Define API endpoints for detailed song information
    lyric_substring = f'getlyric?musicId={id}' 
    
    # Extract lyric from music API response
    lyric: str = ''
    try:
        for request in requests:
            if lyric_substring in request.url:
                lyric_with_time = json.loads(
                    request.response.body
                )['data']['lrclist']
                
                # Form a whole sentence with \n
                for line in lyric_with_time:
                    lyric += f'{line['lineLyric']}\n'
        return lyric
        
    except (KeyError, TypeError):
        print(f'id = {id} failed!')
                    
def filter_comments(
    id: int,
    requests: webdriver.Chrome.requests
) -> list[CommentProfile]:
    """
    Filter comments from requests.

    Args:
        id (int): kuwo_id of the song.
        requests (webdriver.Chrome.requests): Requests from
            certain url.
            
    Returns:
        A list of profiles of comments
    """
    # Define API endpoints for detailed song information
    comment_substring = 'type=get_rec_comment'
    
    comment_list: list[CommentProfile] = []
    
    try:
        for request in requests:
            if comment_substring in request.url:
                with gzip.open(
                    io.BytesIO(request.response.body), 'rb'
                ) as f:
                    # Find comments
                    decompressed_data = f.read().decode('utf-8')
                    datalist = json.loads(decompressed_data)['rows']
                    
                    # Form CommentProfile
                    for comment in datalist:
                        filtered_data = dict()
                        filtered_data['content'] = comment['msg']
                        filtered_data['username'] = comment['u_name']
                        filtered_data['time'] = comment['time']
                        comment_list.append(
                            CommentProfile(**filtered_data)
                        )
        return comment_list
    except (KeyError, TypeError):
        print(f'id = {id} failed!')                
    

def get_song_lyric_and_comment(
    id: int,
    driver: webdriver.Chrome
) -> webdriver.Chrome.requests:
    """
    Scrape song's lyric and comments from target id.

    Args:
        id (int): kuwo_id of the song.
        driver (webdriver.Chrome): Chrome driver to mimic real
                                   human.
    
    Returns:
        webdriver.Chrome.requests from certain url.
    """
    if hasattr(driver, 'requests'):
        del driver.requests
    
    try:
        driver.get(f"https://www.kuwo.cn/play_detail/{id}")
    except exceptions.WebDriverException:
        print(f'id = {id} failed!')
        return None
    
    # Wait for some time
    time.sleep(random.uniform(0.5, 1.0))
    return driver.requests

def read_song_profile(id: int) -> SongProfile:
    """
    Read profile of a song.

    Args:
        id (int): ID of the song

    Returns:
        SongProfile: A SongProfile
    """
    with open(f'./Song/{id}/data.json', 'r', encoding = 'utf-8') as f:
        data = json.loads(f.read())
        return SongProfile(**data)
    
def complete_song(id: int, driver: webdriver.Chrome):
    """
    Complete song's profile

    Args:
        id (int): ID of the song
        driver (webdriver.Chrome): Chrome driver to mimic real
                                   human.
    """
    song_profile = read_song_profile(id)
    requests = get_song_lyric_and_comment(id, driver)
    song_profile.comments = filter_comments(id, requests)
    song_profile.lyrics = filter_lyric(id, requests)
    song_profile.save_to_local()
    print(f'Song {id} successfully saved')
                    
if __name__ == '__main__':
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
    
    MAX_THREADS = 5
    
    threads = []
    
    # Initialize WebDriver
    drivers = []
    for i in range(MAX_THREADS):
        drivers.append(webdriver.Chrome())
    
    song_ids_to_process = []
    for item_name in os.listdir('./Song'):
        song_ids_to_process.append(int(item_name))
    
    for i in range(0, len(song_ids_to_process), MAX_THREADS):
        batch_ids = song_ids_to_process[i:i + MAX_THREADS]
        current_batch_threads = []
        for j, song_id in enumerate(batch_ids):
            thread = threading.Thread(target=complete_song, args=(song_id, drivers[j]))
            threads.append(thread)
            current_batch_threads.append(thread)
            thread.start()
        
        for thread in current_batch_threads:
            thread.join()
        
        print(f"Batch {int(i/MAX_THREADS + 1)} completed")
        time.sleep(random.uniform(2, 3))
    
    for i in range(MAX_THREADS):
        drivers[i].quit()
    