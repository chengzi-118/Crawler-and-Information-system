from django.contrib import admin
from .models import Singer
from django.utils.html import format_html
from song.models import Song

@admin.register(Singer)
class SingerAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Singer model.
    Customizes the display and search functionality in the Django admin interface.
    """
    list_display = ('kuwo_id', 'name', 'region', 'display_songs_list_full')
    search_fields = ('region', 'kuwo_id')
    
    readonly_fields = ('display_songs_list_full',)
    
    def display_songs_list_full(self, obj):
        songs = obj.songs.all()
        if songs:
            song_links = []
            for song in songs:
                link = f'/admin/song/song/{song.kuwo_id}/change/'
                song_links.append(f'<a href="{link}">{song.name}</a>')
            return format_html("<ul>{}</ul>".format("".join([f"<li>{item}</li>" for item in song_links])))
        return "No singer"
        