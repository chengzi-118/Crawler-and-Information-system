from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search_page_view, name='search_page'),
    path('results/', views.search_result_view, name='search_results'),
    path('songs/', views.search_result_view, {'search_type': 'song'}, name='search_songs'),
    path('singers/', views.search_result_view, {'search_type': 'singer'}, name='search_singers'),
]