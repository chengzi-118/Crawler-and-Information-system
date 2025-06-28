import json
from dataclasses import dataclass

@dataclass
class SingerProfile:
    """
    Represents basic information of a singer.
    
    Attributes:
        name(str): The name of the singer.
        id(int): ID of the singer in the kuwo website.
        aartist(str): Another name of the singer, defalts to empty string.
        artistFans(int): Number of fans of the singer, defalts to 0.
        albumNum(int): Number of albums of the singer, defalts to 0.
        mvNum(int): Number of MVs of the singer, defalts to 0.
        musicNum(int): Number of musics of the singer, defalts to 0.
        isStar(int): It seems that this number has no meaning, defalts to 0.
        content_type: It seems that this string has no meaning, defalts to '0'.
        pic(str): URL of a defalt picture(300 * 300) of the singer, defalt to empty string.
    """
    name: str
    id: int
    aartist: str = ''
    artistFans: int = 0
    albumNum: int = 0
    mvNum: int = 0
    musicNum: int = 0
    isStar: int = 0
    content_type: str = '0'
    pic: str = ''

class Singer:
    def __init__(
    self,
    ProfileData: SingerProfile,
):
        pass
        