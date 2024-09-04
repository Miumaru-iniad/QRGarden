from django.shortcuts import render, redirect
from django.http import HttpResponse
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import datetime

# Create your views here.
name_list = {'tomato': 'トマト'}

def top(request, name):
    params = {
        'name': name,
    }
    return render(request, 'myapp/top.html', params)

def chat(request, name):
    params = {
        'name': name,
    }
    return render(request, 'myapp/chat.html', params)

def schedule(request, name):
    params = {
        'name': name_list[name],
    }
    return render(request, 'myapp/schedule.html', params)