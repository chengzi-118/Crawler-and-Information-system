from django.db import models

class Singer(models.Model):
    """
    Represents a singer and its associated information from Kuwo.
    """

    kuwo_id = models.IntegerField(
        primary_key = True,
        verbose_name = "kuwo_id"
    )

    name = models.CharField(
        max_length = 50,
        unique = True,
        verbose_name = "name"
    )
    image = models.ImageField(
        upload_to='Singer',
        verbose_name = "picture"
    )
    info = models.TextField(
        blank = True,
        null = True,
        verbose_name = "information"
    )
    original_image_url = models.URLField(
        max_length=1024,
        blank=True,
        verbose_name="original image URL"
    )
    original_url = models.URLField(
        max_length = 200,
        unique = True,
        verbose_name="original URL"
    )

    fan_num = models.IntegerField(
        default = 0,
        verbose_name = "number of fans"
    )
    album_num = models.IntegerField(
        default = 0,
        verbose_name = "number of albums"
    )
    mv_num = models.IntegerField(
        default = 0,
        verbose_name = "number of MVs"
    )
    music_num = models.IntegerField(
        default = 0,
        verbose_name = "number of musics"
    )
    
    alias = models.CharField(
        max_length = 50,
        blank = True,
        null = True,
        verbose_name = "another name"
    )
    birthday = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="birthday"
    )
    birthplace = models.CharField(
        max_length=50,
        blank=True, 
        null=True, 
        verbose_name="birthplace"
    )
    region = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        verbose_name="region"
    )
    gender = models.CharField(
        max_length=10, 
        blank=True, 
        null=True, 
        verbose_name="gender"
    )
    weight = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name="weight"
    )
    height = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name="height"
    )
    language = models.CharField(
        max_length=50,
        blank=True, 
        null=True, 
        verbose_name="language"
    )
    constellation = models.CharField(
        max_length=50,
        blank=True, 
        null=True, 
        verbose_name="constellation"
    )
    
    def __str__(self) -> str:
        """
    Returns the string representation of the Singer object.
        """
        return self.name
    