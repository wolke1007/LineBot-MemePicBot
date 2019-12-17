# -*- coding: utf-8 -*-
import random
from flask import Flask, request, abort
from linebot import WebhookHandler
from linebot.exceptions import (
    InvalidSignatureError
)
from config import *
from models.bot.bot import Bot
from models.chat import Chat


app = Flask(__name__)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
API_URL = 'https://api.imgur.com/'
MASHAPE_URL = 'https://imgur-apiv3.p.mashape.com/'


@app.route("/callback", methods=['POST'])
def callback(event):
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 上傳圖片這邊有兩種做法，可行性上在後面討論
# 1. 先上傳圖片，後命名剛剛圖片的名稱
# 2. 先命名圖片名稱，後上傳圖片
# ~~~~~~先講結論~~~~~ 最後決定採用 2，也就是採取先命名後上傳
# 探討幾種 1 的實作方式以及我覺得不適用原因:
# 1. 將圖片暫存在 memory 於命名後拿來上傳，但因為線上會起多個 thread 跑程式有機會是另一個 thread 去詢問而拿不到圖片
#    另外也可能會有 memory 不足的問題
# 2. 有考慮用寫檔方式儲存暫存檔，但 Google Cloud Function 不支援寫檔操作所以無法
# 3. 先存圖片到 DB 之後命名並上傳，但這將會增加 DB Server 傳輸負擔跟流量成本
# 4. 只要收到圖片一律上傳，如果仍未命名但又有收到圖片，就刪除前一張後再上傳，直到有命名則修改最後一張上傳圖片的名稱為正式名稱
#    但這會增加上傳的成本，依據 Imgur 免費的流量只能上傳 10,000 張圖片每月，就算花 25 鎂也是 60,000 每月，並不能這樣玩
# 最後決定，只能確認使用者有先命名完才做上傳動作，確保每一次有確定要上傳才做
# 與此同時，有考慮每個人是不是要設定 quota 來限制是不是一天只能上傳幾張圖片(目前沒此設計)
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    chat = Chat(event, is_image_event=True)
    bot = Bot(chat)
    del chat, bot

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event, is_image_event=False):
    chat = Chat(event)
    bot = Bot(chat)
    del chat, bot
