from django.shortcuts import render, redirect
from django.http import HttpResponse
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os
from django.conf import settings

# Create your views here.
name_list = {'tomato': 'トマト'}

def top(request, crop_name_en):
    params = {
        'crop_name_en': crop_name_en,
        'crop_name_ja': name_list[crop_name_en],
    }
    return render(request, 'myapp/top.html', params)

from django.shortcuts import render, redirect
from django.http import HttpResponse
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os
from django.conf import settings

name_list = {'tomato': 'トマト'}

def top(request, crop_name_en):
    params = {
        'crop_name_en': crop_name_en,
        'crop_name_ja': name_list[crop_name_en],
    }
    return render(request, 'myapp/top.html', params)

def chat(request, crop_name_en):
    crop_name_ja = name_list.get(crop_name_en, "不明な作物")
    
    # セッションにチャット履歴がなければ初期化
    if 'chat_history' not in request.session:
        request.session['chat_history'] = []

    if request.method == 'POST':
        # ユーザーのメッセージを取得
        user_message = request.POST.get('message')
        if user_message:
            # ユーザーのメッセージを履歴に追加
            request.session['chat_history'].append({'sender': 'user', 'message': user_message})

            # チャットボットの応答（ダミー）
            bot_response = "これはチャットボットの応答です。"
            request.session['chat_history'].append({'sender': 'bot', 'message': bot_response})

            # 最大3往復（6メッセージ）まで保持
            if len(request.session['chat_history']) > 6:
                request.session['chat_history'] = request.session['chat_history'][-6:]

            # セッションの変更を保存
            request.session.modified = True

        # 同じページにリダイレクトして入力フォームをリセット
        return redirect('chat', crop_name_en=crop_name_en)

    params = {
        'crop_name_en': crop_name_en,
        'crop_name_ja': crop_name_ja,
        'chat_history': request.session['chat_history']
    }

    return render(request, 'myapp/chat.html', params)

def schedule(request, crop_name_en):
    params = {
        'crop_name_en': crop_name_en,
        'crop_name_ja': name_list[crop_name_en],
    }
    return render(request, 'myapp/schedule.html', params)

# Google Calendar API認証を開始
def authorize(request):
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri=request.build_absolute_uri('https://403bb8645a0b463cbbef8fc76f74b11e.vfs.cloud9.us-west-1.amazonaws.com/oauth2callback/')  # コールバックURL
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    request.session['state'] = state
    return redirect(authorization_url)

# OAuth 2.0 コールバック
def oauth2callback(request):
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    state = request.session.get('state')
    
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        state=state,
        redirect_uri=request.build_absolute_uri('https://403bb8645a0b463cbbef8fc76f74b11e.vfs.cloud9.us-west-1.amazonaws.com/oauth2callback/')
    )
    
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    
    credentials = flow.credentials
    request.session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    return redirect('calendar_api', crop_name_en='tomato')

# Google Calendar APIにアクセス
def calendar_api(request, crop_name_en):
    credentials_data = request.session.get('credentials')

    if not credentials_data:
        return redirect('authorize')

    creds = Credentials(
        token=credentials_data['token'],
        refresh_token=credentials_data['refresh_token'],
        token_uri=credentials_data['token_uri'],
        client_id=credentials_data['client_id'],
        client_secret=credentials_data['client_secret'],
        scopes=credentials_data['scopes']
    )

    service = build('calendar', 'v3', credentials=creds)

    if request.method == 'POST':
        start_date_str = request.POST.get('start_date')
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

        events = [
            {
                'summary': '種まき',
                'description': '種をまきましょう\nexample.com',
                'start': {
                    'date': start_date.strftime('%Y-%m-%d'),
                    'timeZone': 'Asia/Tokyo',
                },
                'end': {
                    'date': (start_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                    'timeZone': 'Asia/Tokyo',
                },
            },
            {
                'summary': '追肥',
                'description': '追肥をしましょう\nexample.com',
                'start': {
                    'date': (start_date + timedelta(days=10)).strftime('%Y-%m-%d'),
                    'timeZone': 'Asia/Tokyo',
                },
                'end': {
                    'date': (start_date + timedelta(days=15)).strftime('%Y-%m-%d'),
                    'timeZone': 'Asia/Tokyo',
                },
            },
        ]

        for event in events:
            created_event = service.events().insert(calendarId='primary', body=event).execute()
            print('Event created: %s' % (created_event.get('htmlLink'))) 
        
    params = {
        'crop_name_en': crop_name_en,
        'crop_name_ja': name_list[crop_name_en],
    }
    return render(request, 'myapp/schedule.html', params)