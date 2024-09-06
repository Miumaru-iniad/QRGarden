from django.shortcuts import render, redirect
from django.http import HttpResponse
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os
from django.conf import settings

# OpenAI関連のimport
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ChromaDB関連のimport
import chromadb
from chromadb.config import Settings

# Qdrant関連のimport
import qdrant_client
from langchain_qdrant import Qdrant

from langchain.vectorstores import Chroma

name_list = {'tomato': 'トマト'}


def top(request, crop_name_en):
    params = {
        'crop_name_en': crop_name_en,
        'crop_name_ja': name_list[crop_name_en],
    }
    return render(request, 'myapp/top.html', params)


# OpenAIのAPIキーとエンドポイント
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_API_BASE = "https://api.openai.iniad.org/api/v1/"





# ドキュメントのフォーマット
def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])

# RAGによる回答生成
def generate_response(user_question):

    embeddings_model = OpenAIEmbeddings(
    openai_api_base= OPENAI_API_BASE
)
    db = Chroma(persist_directory="DB",embedding_function=embeddings_model)

    # OpenAI LLMの設定
    LLM = ChatOpenAI(model_name="gpt-4o-mini", temperature=1, verbose=True, openai_api_key=OPENAI_API_KEY, openai_api_base=OPENAI_API_BASE)

    # Qdrantから関連ドキュメントを取得
    retriever = db.as_retriever()

    # プロンプトテンプレート
    template = """
    関連するドキュメントを基に、回答を生成してください。
    マークダウン記法は使用しないでください。
    # {context}

    Question : {question}
    Answer : 
    """
    prompt = ChatPromptTemplate.from_template(template)

    # チェーンの構築
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | LLM
        | StrOutputParser(verbose=True)
    )

    # ドキュメント検索と回答生成の実行
    references = retriever.invoke(user_question)
    if not references:
        return "関連ドキュメントが見つかりませんでした。"

    # RAGによる最終応答の生成
    output_by_retriever = chain.invoke(user_question)

    # ここからリンク埋め込み処理を追加
    products = {
        "INIAD-UP": "https://iniad-crops-seles.vercel.app/product/up",
        "INIA土": "https://iniad-crops-seles.vercel.app/product/soil",
        "INIAD-BUG-BLOCKER": "https://iniad-crops-seles.vercel.app/product/bug-blocker"
    }

    # 回答中に製品名が含まれていた場合、リンクに置換し、改行されず、新しいタブで開くように設定
    for product, url in products.items():
        output_by_retriever = output_by_retriever.replace(
            product, f'<a href="{url}" target="_blank" style="color: blue; white-space: nowrap;">{product}</a>'
        )

    return output_by_retriever


def chat(request, crop_name_en):
    crop_name_ja = "トマト"  # 例としてトマトに固定
    
    # セッションにチャット履歴がなければ初期化
    if 'chat_history' not in request.session:
        request.session['chat_history'] = []

    if request.method == 'POST':
        # ユーザーの質問を取得
        user_message = request.POST.get('message')

        if user_message:
            # RAGで回答を生成
            bot_response = generate_response(user_message)

            # ユーザーのメッセージを履歴に追加
            request.session['chat_history'].append({'sender': 'user', 'message': user_message})
            request.session['chat_history'].append({'sender': 'bot', 'message': bot_response})

            if len(request.session['chat_history']) > 2:
                request.session['chat_history'] = request.session['chat_history'][-2:]

            # セッションの変更を保存
            request.session.modified = True

            # リダイレクトしてフォームをリセット
            return redirect('chat', crop_name_en=crop_name_en)

    # チャット画面を表示
    params = {
        'crop_name_en': crop_name_en,
        'crop_name_ja': crop_name_ja,
        'chat_history': request.session.get('chat_history', [])
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