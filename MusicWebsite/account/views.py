from django.shortcuts import render, redirect
from django.urls import reverse
from song import views as song_views 
from singer import views as singer_views

def home_redirect_view(request):
    """
    Check whether the user has set user name.
    If not, redirect to setting page.
    """
    if 'username' not in request.session or not request.session['username']:
        return redirect('account:set_username')
    else:
        return song_views.home_page_view(request)

def singer_redirect_view(request):
    """
    Check whether the user has set user name.
    If not, redirect to setting page.
    """
    if 'username' not in request.session or not request.session['username']:
        return redirect('account:set_username')
    else:
        return singer_views.singer_list(request)

def set_username_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'set_username':
            username = request.POST.get('username', '').strip()
            if username:
                request.session['username'] = username
                return redirect('/')
            else:
                current_username = request.session.get('username', '')
                return render(
                    request,
                    'account/set_username.html',
                    {
                        'error_message': 'Empty Username',
                        'current_username': current_username
                    }
                )
        elif action == 'clear_username':
            if 'username' in request.session:
                del request.session['username']
            return redirect('/')
    else:
        current_username = request.session.get('username', '')
        return render(request, 'account/set_username.html', {'current_username': current_username})