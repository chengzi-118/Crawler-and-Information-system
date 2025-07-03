from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('', views.set_username_view, name = 'set_username'),
]