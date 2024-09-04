from django.shortcuts import render, redirect
from django.http import HttpResponse

# Create your views here.
name_list = {'tomato': 'トマト'}

def top(request, name):
    params = {
        'name': name_list[name],
    }
    return render(request, 'myapp/top.html', params)

def chat(request, name):
    params = {
        'name': name_list[name],
    }
    return render(request, 'myapp/chat.html', params)

def schedule(request, name):
    params = {
        'name': name_list[name],
    }
    return render(request, 'myapp/schedule.html', params)