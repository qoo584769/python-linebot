import os
import re
import requests
import json
import time

from dotenv import load_dotenv
from bs4 import BeautifulSoup
from flask import Flask, Blueprint, jsonify, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    ImageMessage,
    URIAction,
    MessageAction,
    PostbackAction,    
    MessagingApiBlob,
    RichMenuRequest,
    RichMenuArea,
    RichMenuSize,
    RichMenuBounds,
    RichMenuSwitchAction,
    CreateRichMenuAliasRequest
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, PostbackEvent, FollowEvent 

import yfinance as yf

from models.member_model import Member

line_bot_bp = Blueprint('linebotApi', __name__)

# 載入 .env 文件
load_dotenv()

# LINE Bot credentials
line_channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
line_channel_secret = os.getenv('LINE_CHANNEL_SECRET')

# 設定 LINE API 客戶端
config = Configuration(access_token=line_channel_access_token)
api_client = ApiClient(configuration=config)
messaging_api = MessagingApi(api_client)
line_bot_blob_api = MessagingApiBlob(api_client)
handler = WebhookHandler(line_channel_secret)

@line_bot_bp.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 建立並上傳快速選單
def create_rich_menu():
    rich_menu_size = RichMenuSize(width=2500, height=1686)

    # 定義快速選單的區域
    rich_menu_areas = [
        RichMenuArea(
            bounds=RichMenuBounds(x=0, y=0, width=833, height=843),
            action=MessageAction(text="雷達回波")
            # action=PostbackAction(label="Option 1", text="雷達回波", data="option1")
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=834, y=0, width=833, height=843),
            action=MessageAction(text="雷達回波圖")
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=1668, y=0, width=832, height=843),
            action=MessageAction(text="電影")
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=0, y=834, width=833, height=843),
            action=MessageAction(text="雷達回波")
            # action=PostbackAction(label="Option 1", text="雷達回波", data="option1")
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=834, y=834, width=833, height=843),
            action=PostbackAction(label="Option 2",text="雷達回波圖", data="option2")
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=1668, y=834, width=832, height=843),
            action=PostbackAction(label="Option 3",text="雷達回波", data="option3")
        )
    ]

    rich_menu_request = RichMenuRequest(
        size=rich_menu_size,
        selected=True,
        name="Radar Menu",
        chatBarText="Tap here",
        # chat_bar_text="Tap here",
        areas=rich_menu_areas
    )

    # 上傳快速選單
    try:
        rich_menu_id = messaging_api.create_rich_menu(rich_menu_request).rich_menu_id
        # 設定快速選單的圖片（從指定 URL 下載圖片）
        image_url = "https://lh3.googleusercontent.com/u/0/d/16j1QjN-iFbTvJhfte647MZCXDvaoJlDr=w1358-h688-iv1"

        image_response = requests.get(image_url)
        
        if image_response.status_code == 200:
            with open("rich_menu_image.png", "wb") as f:
                f.write(image_response.content)
            with open("rich_menu_image.png", "rb") as f:
                image_bytes = bytearray(f.read())
                line_bot_blob_api.set_rich_menu_image(rich_menu_id,body=image_bytes,  _headers={'Content-Type': 'image/png'})
            # 設定為預設快速選單
            set_default_rich_menu(rich_menu_id)
        else:
            print("Failed to download image.")
    except Exception as e:
        print("Error creating rich menu:", e)
    
def set_default_rich_menu(rich_menu_id):
  try:
    messaging_api.set_default_rich_menu(rich_menu_id)
    print('建立預設快速選單成功')
  except Exception as e:
    print("建立預設快速選單發生錯誤：", e)

# 取得全部圖文列表並刪除
def get_rich_menu_list():
    rich_menu_list = messaging_api.get_rich_menu_list()
    menu_list_len = len(rich_menu_list.richmenus)
    for index,rich_menu in enumerate(rich_menu_list.richmenus):
      if index != menu_list_len - 1:
        messaging_api.delete_rich_menu(rich_menu.rich_menu_id)
      else:
        create_rich_menu()

def get_stock_info(symbol):
  stock = yf.Ticker(symbol)
  todays_data = stock.history(period='1d')
  if not todays_data.empty:
      # 取得收盤價
      return todays_data['Close'][0]  
  return None

def text_match(text):
  role_logon = re.compile(r'([註冊帳號]+|[註冊]+|[\da-zA-Z+-_]+@[\da-zA-Z-]+\.[\da-zA-Z-]+|[\da-zA-Z_+-]+)')
  role_email= re.compile(r'[\da-zA-Z+-_]+@[\da-zA-Z-]+\.[\da-zA-Z-]+')
  role_username = re.compile(r'([\da-zA-Z+-_]+(?=@))')
  # role_password = re.compile(r'\s+[\da-zA-Z_+-]+$')

  find_logon_text = role_logon.findall(text)
  find_email_text = role_email.findall(find_logon_text[1]) if len(find_logon_text) > 1 else find_logon_text[0]

  email = find_logon_text[1] if len(find_logon_text) > 1 else find_logon_text[0]

  match text:
    case text if text.startswith('註冊') and not len(find_email_text):
      return '信箱格式錯誤'

    case text if text.startswith('註冊') and len(find_logon_text) != 3:
      return '請在信箱後面空一格輸入密碼'

    case text if text.startswith('註冊') and Member.exists(email):
      return '帳號已存在'

    case text if text.startswith('註冊'):
      username = role_username.findall(find_logon_text[1])
      password = find_logon_text[2]
      Member.create(username, password, email)
      return '註冊成功'

    case text if get_stock_info(text) is not None :
      return f"{text} 收盤價格: ${get_stock_info(text):.2f}"

    case _:
      return '輸入訊息未觸發任何功能'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip()
    msg_type=event.message.type
    user_id = event.source.user_id

    if msg_type == 'text':
      if text == '雷達回波圖' or text == '雷達回波':
        messaging_api.push_message( PushMessageRequest(
        to=user_id,
        messages=[TextMessage(text='取得資料中....')]
        )) 
        img_url = f'https://cwaopendata.s3.ap-northeast-1.amazonaws.com/Observation/O-A0058-001.png?{time.time_ns()}'

        img_message = ImageMessage(original_content_url=img_url, preview_image_url=img_url)

        reply_request = ReplyMessageRequest(
        reply_token=event.reply_token,
        messages=[img_message]
        )

        messaging_api.reply_message(reply_request) 
      
      if text == '電影':
        url = os.getenv('MOVIE_REMOTE_URL')
        messaging_api.push_message( PushMessageRequest(
        to=user_id,
        messages=[TextMessage(text='正在啟動電影API....')]
        )) 
        api_url = f'{url}/api/movie'
        response = requests.get(api_url)

        if response.status_code == 200: 
          reply_text = '啟動成功'
         
        reply_text = '啟動失敗'

        reply_request = ReplyMessageRequest(
        reply_token=event.reply_token,
        messages=[TextMessage(text=reply_text)]
        )
        messaging_api.reply_message(reply_request)

      else:
        reply_text = text_match(text)

        reply_request = ReplyMessageRequest(
        reply_token=event.reply_token,
        messages=[TextMessage(text=reply_text)]
        )
        messaging_api.reply_message(reply_request)

@handler.add(FollowEvent)
def handle_follow(event):
    pass

get_rich_menu_list()