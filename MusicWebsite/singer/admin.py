from django.contrib import admin
from .models import Singer

@admin.register(Singer)
class SingerAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Singer model.
    Customizes the display and search functionality in the Django admin interface.
    """
    list_display = ('kuwo_id', 'name', 'region', 'music_num', 'fan_num', 'original_url')
    search_fields = ('name', 'region', 'kuwo_id')