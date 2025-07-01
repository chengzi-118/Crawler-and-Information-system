from dataclasses import dataclass, field, asdict
import os
import requests
import json

# Define the base directory for saving singer data
save_dir = './Singer/'

@dataclass
class SingerProfile:
    """
    Represents detailed information of a singer.
    
    Attributes:
        name(str): The name of the singer.
        id(int): ID of the singer in the kuwo website, default to -1.
        aartist(str): Another name of the singer, defaults to empty string.
        artistFans(int): Number of fans of the singer, defaults to 0.
        albumNum(int): Number of albums of the singer, defaults to 0.
        mvNum(int): Number of MVs of the singer, default to 0.
        musicNum(int): Number of musics of the singer, defaults to 0.
        pic(str): URL of a default picture(300 * 300) of the singer,
                  default to empty string.
        birthday(str): Birthday of the singer.
        birthplace(str): Birthplace of the singer.
        region(str): Region of the singer.
        gender(str): Gender of the singer.
        weight(str): Weight of the singer.
        height(str): Height of the singer.
        language(str): Language of the singer.
        constellation(str): Constellation(星座) of the singer.
        info(str): Detailed information of the singer.
        song_list(list[int]): Dict of songs' name and id of the singer.
        original_url(str): URL can be clicked to navigate to the original page.
    """
    name: str = ''
    id: int = -1
    aartist: str = ''
    artistFans: int = 0
    albumNum: int = 0
    mvNum: int = 0
    musicNum: int = 0
    pic: str = ''
    birthday: str = ''
    birthplace: str = ''
    region: str = ''
    gender: str = ''
    weight: str = ''
    height: str = ''
    language: str = ''
    constellation: str = ''
    info: str = ''
    song_list: list = field(default_factory = list)
    original_url: str = ''
    
    def save_to_local(self):
        """Saves singer's profile data to a JSON file."""
        
        # Construct singer-specific folder path
        os.makedirs(save_dir + str(self.id), exist_ok = True)
        
        json_file_path = save_dir + str(self.id) + '/data.json'
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, indent=4, ensure_ascii=False)
            
    def save_picture(self):
        """Downloads and saves the singer's profile picture."""
        response = requests.get(self.pic)
        category = self.pic.split('.')[-1]
        with open(save_dir + str(self.id) + '/pic.' + category, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
