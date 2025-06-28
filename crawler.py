import requests
from bs4 import BeautifulSoup
import re
import json
from Singer import SingerProfile, Singer, SingerDetail

def get_singers(
    category: int,
    page: int
) -> list[SingerProfile]:
    """
    Gets a list of strings from kuwo music.
    
    This function sends a request to the base url,
    then receives the response and uses the response to get information of singers.
    
    Args:
        category(int): According to the website,0 means 全部歌手, 1 means 华语男 and 2 means 华语女.
        page(int): The page number in the website
        
    Returns:
        list[SingerProfile]: A list of SingerProfile containing basic information of a singer.
        If any error is raised, the function will return an empty list.
    """
    base_url = "https://wapi.kuwo.cn/api/www/artist/artistInfo"
    # HTTP parameters for the API request.
    params = {
        "category": category,
        "prefix": "",
        "pn": page,
        "rn": 60,
        "httpsStatus": 1,
        "reqId": "283aacd0-52a9-11f0-8edc-656bca46e1b4",
        "plat": "web_www",
        "from": ""
    }
    # Custom HTTP headers to mimic a browser request and avoid anti-scraping measures.
    headers = {
        "Accept": "application/json, text/plain,",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Origin": "https://www.kuwo.cn",
        "Referer": "https://www.kuwo.cn/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        ),
        "sec-ch-ua": (
            '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"'
        ),
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows"
    }
    
    response = requests.get(base_url, params = params, headers = headers)
    if response.status_code != requests.codes.ok:
        return []
    
    soup = BeautifulSoup(response.text, features = "lxml")
    p_tag = soup.find('p')
    
    # <p> tag contains the list of artists
    if p_tag:
        json_str = p_tag.get_text()
        
        try:
            data = json.loads(json_str)['data']['artistList']
        except json.JSONDecodeError:
            # If the response is not in json form
            return [] 
        except KeyError:
            # If the response doesn't have 'artistList'
            return []
        
        singer_profiles: list[SingerProfile] = []
        
        # Iterate through data to transfer json to SingerProfile
        for singer_data_dict in data:
            try:
                singer_profile = SingerProfile(**singer_data_dict)
                singer_profiles.append(singer_profile)
            except TypeError:
                # If the singer_data_dict cannot match the SingerProfile
                continue
        
        return singer_profiles
    else:
        # If no <p> tag is found
        return []
