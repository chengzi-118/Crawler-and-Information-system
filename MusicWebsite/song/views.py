from django.shortcuts import render
from .models import Song
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def home_page_view(request):
    all_songs = Song.objects.all().order_by('name')

    paginator = Paginator(all_songs, 20)
    page_number = request.GET.get('page')
    try:
        songs = paginator.page(page_number)
    except PageNotAnInteger:
        songs = paginator.page(1)
    except EmptyPage:
        songs = paginator.page(paginator.num_pages)

    context = {
        'songs': songs,
        'page_obj': songs,
    }
    return render(request, 'song\home_page.html', context)
