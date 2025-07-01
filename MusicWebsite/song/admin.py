from django.contrib import admin
from .models import Song

@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Song model.
    Customizes the display and search functionality
    in the Django admin interface.
    """
    list_display = ('name', 'kuwo_id', 'singer', 'album_name', 'duration')
    search_fields = ('name', 'album_name')
