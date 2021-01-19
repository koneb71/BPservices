from django.shortcuts import render


def index(request):
    ctx = {
        'title': 'Home'
    }
    return render(request, 'index.html', ctx)