from django.shortcuts import render, redirect, get_object_or_404
from .models import Song
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from django.db.models.functions import Length
import datetime
from django.urls import reverse
import uuid

list_num: int = 30

def home_page_view(request):
    """
    Show songs in home page.
    """
    all_songs = Song.objects.annotate(comments_length=Length('comments')).order_by('-comments_length') 

    paginator = Paginator(all_songs, list_num)
    page_number = request.GET.get('page')
    try:
        songs = paginator.page(page_number)
    except PageNotAnInteger:
        songs = paginator.page(1)
    except EmptyPage:
        songs = paginator.page(paginator.num_pages)

    page_obj = paginator.get_page(page_number)

    context = {
        'songs': songs,
        'page_obj': songs,
        'current_page_num': page_obj.number, 
    }
    return render(request, 'song/home_page.html', context)

def change_display_num(request):
    """
    Changes the number of songs in one page and redirect to home page.
    """
    global list_num
    action = request.POST.get('action')
    if action == 'change':
        try:
            num = int(request.POST.get('display_num', '').strip())
            if num <= 0:
                raise ValueError
        except (ValueError, KeyError, TypeError):
            return redirect('song:home_page')
        list_num = num
        return redirect('song:home_page')
    
def song_detail_view(request, song_id):
    if 'username' not in request.session or not request.session['username']:
        return redirect('/account/')
    song = get_object_or_404(Song, pk = song_id)
    
    current_page = request.GET.get('page', 1)
    
    current_username = request.session['username']
    
    comment_content = ''

    if request.method == 'POST':
        # Get comment content
        comment_content = request.POST.get('comment_content', '').strip()
        if comment_content:
            new_comment = {
                'id': str(uuid.uuid4()), 
                'username': current_username,
                'content': comment_content,
                'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            song.comments.insert(0, new_comment)
            song.save()
            return redirect(f"{reverse('song:song_detail', kwargs={'song_id': song.pk})}?page={current_page}")
        
    processed_comments = []
    for comment in song.comments:
        if 'id' not in comment:
            comment['temp_id'] = str(uuid.uuid4())
        else:
            comment['temp_id'] = comment['id']
        processed_comments.append(comment)
        
    if processed_comments:
        processed_comments.sort(key = lambda x: x['time'], reverse = True)
    
    context = {
        'song': song,
        'comments': processed_comments,
        'current_page': current_page,
        'current_username': current_username,
        'comment_content': ''
    }
    return render(request, 'song/song_detail.html', context)

def delete_comment(request, comment_id):
    """
    Delete comments.
    """
    if request.method == 'POST':
        song_id = request.POST.get('song_id')
        comment_username = request.POST.get('comment_username')
        comment_content_match = request.POST.get('comment_content_match')
        comment_time_match = request.POST.get('comment_time_match')
        
        song = get_object_or_404(Song, pk=song_id)
        current_page = request.GET.get('page', 1)

        comments_list = song.comments[:]
        comment_removed = False
        
        for i, comment in enumerate(comments_list):
            if (comment.get('username') == comment_username and
                comment.get('content') == comment_content_match and
                comment.get('time') == comment_time_match):
                    
                comments_list.pop(i)
                comment_removed = True
                break
        
        if comment_removed:
            song.comments = comments_list
            song.save()
        
        return redirect(f"{reverse('song:song_detail', kwargs={'song_id': song.pk})}?page={current_page}")
    else:
        return redirect('song:home_page')
