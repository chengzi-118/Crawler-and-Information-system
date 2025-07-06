from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Singer

list_num: int = 12

def singer_list(request):
    all_singers = Singer.objects.all().order_by('-fan_num')

    paginator = Paginator(all_singers, list_num)
    page_number = request.GET.get('page')
    try:
        singers = paginator.page(page_number)
    except PageNotAnInteger:
        singers = paginator.page(1)
    except EmptyPage:
        singers = paginator.page(paginator.num_pages)
        
    page_obj = paginator.get_page(page_number)

    context = {
        'singers': singers,
        'page_obj': singers,
        'current_page_num': page_obj.number, 
    }
    return render(request, 'singer/singer_list.html', context) 

def change_display_num(request):
    """
    Changes the number of singers in one page and redirect to the first page.
    """
    global list_num
    action = request.POST.get('action')
    if action == 'change':
        try:
            num = int(request.POST.get('display_num', '').strip())
            if num <= 0:
                raise ValueError
        except (ValueError, KeyError, TypeError):
            return redirect('singer:singer_list')
        list_num = num
        return redirect('singer:singer_list')

def singer_detail_view(request, singer_id):
    if 'username' not in request.session or not request.session['username']:
        return redirect('/account/')
    singer = get_object_or_404(Singer, pk = singer_id)
    
    current_page = request.GET.get('singer_page', 1)

    context = {
        'singer': singer,
        'current_page': current_page,
    }
    return render(request, 'singer/singer_detail.html', context)
