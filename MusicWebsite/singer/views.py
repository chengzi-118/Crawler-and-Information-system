from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Singer

def singer_list(request):
    all_singers = Singer.objects.all().order_by('name')

    paginator = Paginator(all_singers, 20)
    page_number = request.GET.get('page')
    try:
        singers = paginator.page(page_number)
    except PageNotAnInteger:
        singers = paginator.page(1)
    except EmptyPage:
        singers = paginator.page(paginator.num_pages)

    context = {
        'singers': singers,
        'page_obj': singers,
    }
    return render(request, 'singer/singer_list.html', context) 