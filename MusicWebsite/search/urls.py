from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.SearchPageView.as_view(), name='search_page'),
    path('results/', views.SearchResultsView.as_view(), name='search_results'),
    path('songs/', views.SearchResultsView.as_view(), {'search_type': 'song'}, name='search_songs'),
    path('singers/', views.SearchResultsView.as_view(), {'search_type': 'singer'}, name='search_singers'),
]