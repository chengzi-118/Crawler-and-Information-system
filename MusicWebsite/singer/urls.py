from django.urls import path
from . import views

app_name = 'singer'
urlpatterns = [
    path('', views.singer_list, name='singer_list'),
]