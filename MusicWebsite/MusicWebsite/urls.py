"""
URL configuration for MusicWebsite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from account import views as account_views 
from django.views.generic.base import RedirectView
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', account_views.home_redirect_view, name='home_redirect'), 
    path('songs/', include('song.urls')), 
    path('singers/', account_views.singer_redirect_view, name='singer_list_redirect'), 
    path('singers/', include('singer.urls')),
    path('account/', include('account.urls')), 
    path('search/', account_views.search_redirect_view, name='search_redirect'), 
    path("search/", include('search.urls', namespace='search')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)