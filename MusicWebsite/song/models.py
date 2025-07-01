from django.db import models

class Song(models.Model):
    """
    Represents a song and its associated information from Kuwo.
    """

    kuwo_id = models.IntegerField(
        primary_key = True,
        verbose_name = "kuwo_id",
        default = -1
    )
    
    name = models.CharField(
        max_length = 100,
        verbose_name = "name",
        default = ''
    )
    image = models.ImageField(
        upload_to = '',
        verbose_name = "picture",
        default = ''
    )
    original_image_url = models.URLField(
        max_length=1024,
        blank=True,
        null=True,
        verbose_name="original image URL"
    )
    original_url = models.URLField(
        max_length = 200,
        unique = True,
        default = '',
        verbose_name="original URL"
    )
    
    release_date = models.CharField(
        max_length = 50,
        blank = True,
        null = True,
        verbose_name = "release date"
    )
    
    duration = models.IntegerField(
        verbose_name = "seconds of the song",
        default = -1
    )
    
    album_name = models.CharField(
        max_length = 50,
        blank = True,
        null = True,
        verbose_name = "album name"
    )
    
    lyrics= models.TextField(
        max_length = 5000,
        blank = True,
        null = True,
        verbose_name = "lyrics"
    )
    
    comments = models.JSONField(
        default=list, 
        blank=True, 
        help_text="list of comments"
    )
    
    singer = models.ForeignKey(
        'singer.Singer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='songs',
        verbose_name="singer"
    )
    
    def __str__(self) -> str:
        """
            Returns the string representation of the Song object.
        """
        return f"{self.name}"