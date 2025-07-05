from django.urls import path
from . import views

app_name = 'song'

urlpatterns = [
    path('', views.home_page_view, name='home_page'),
    path('change-display-num/', views.change_display_num, name='change_display_num_url'),
    path('comment/<str:comment_id>/delete/', views.delete_comment, name='delete_comment'), 
    path('<int:song_id>/', views.song_detail_view, name='song_detail')
]