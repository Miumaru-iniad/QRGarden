from django.shortcuts import render, redirect
from django.http import HttpResponse
from google_auth_oauthlib.flow import InstalledAppFlow
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

            # 最大3往復（6メッセージ）まで保持
            if len(request.session['chat_history']) > 6:
                request.session['chat_history'] = request.session['chat_history'][-6:]

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

def calendar_api(request, crop_name_en):
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
        
        params = {
            'crop_name_en': crop_name_en,
            'crop_name_ja': name_list[crop_name_en],
        }
        return render(request, 'myapp/schedule.html', params)