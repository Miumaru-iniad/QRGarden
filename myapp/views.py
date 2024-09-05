from django.shortcuts import render, redirect
from django.http import HttpResponse
from google_auth_oauthlib.flow import InstalledAppFlow
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

def calendar_api(request, crop_name_en):
    if request.method == 'POST':
        start_date_str = request.POST.get('start_date')
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

        SCOPES = ['https://www.googleapis.com/auth/calendar']
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        service = build('calendar', 'v3', credentials=creds)

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
        
        return redirect(os.path.join(settings.REDIRECT_URL, crop_name_en))


def schedule(request, crop_name_en):
    params = {
        'crop_name_en': crop_name_en,
        'crop_name_ja': name_list[crop_name_en],
    }
    return render(request, 'myapp/schedule.html', params)

def calendar_api(request, crop_name_en): #トマト
    if request.method == 'POST':
        start_date_str = request.POST.get('start_date')
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

        # カレンダーAPIのスコープを設定
        SCOPES = ['https://www.googleapis.com/auth/calendar']

        # ユーザー認証を行いAPIクライアントを作成
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)

        service = build('calendar', 'v3', credentials=creds)

        # イベントデータを作成
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

        # イベントを追加
        for event in events:
            created_event = service.events().insert(calendarId='primary', body=event).execute()
            print('Event created: %s' % (created_event.get('htmlLink'))) 
        
        return redirect(os.path.join(settings.REDIRECT_URL, crop_name_en))