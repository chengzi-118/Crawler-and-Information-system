from dataclasses import dataclass, field, asdict
import os
import requests
import json

# Define the base directory for saving singer data
save_dir = './Song/'

@dataclass
class SongProfile:
    """
    Represents detailed information for a song.
                                                                               
    Attributes:
        name (str): The name of the song.
        id (int): Unique ID of the song on the Kuwo Music website;
                  defaults to -1 if not available.
        artist (str): The name of the song's artist.
        artistid (int): Unique ID of the song's artist;
                        defaults to 0 if not available.
        pic (str): URL for the song's cover image;
                   defaults to an empty string.
        releasedate (str): The release date of the song.
        duration (int): The duration of the song in seconds.
        album (str): The album the song belongs to.
        original_url (str): Direct URL to the song's original page.
        lyrics (str): The lyrics of the song.
        comments (list[str]): A list of comments for the song.
    """
    name: str = ''
    id: int = -1
    artist: str = ''
    artistid: int = 0
    pic: str = ''
    releasedate: str = ''
    duration: int = 0
    album: str = ''
    original_url: str = ''
    lyrics: str = ''
    comments: list = field(default_factory=list)
    
    def save_to_local(self):
        """Saves song's profile data to a JSON file."""
        
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