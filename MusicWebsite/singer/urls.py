from django.urls import path
from . import views

app_name = 'singer'
urlpatterns = [
    path('', views.singer_list, name='singer_list'),
    path('change-display-num/', views.change_display_num, name='change_display_num_url'),
    path('<int:singer_id>/', views.singer_detail_view, name='singer_detail')
]