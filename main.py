# -*- coding: utf-8 -*-
import random
from flask import Flask, request, abort
from linebot import WebhookHandler
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage
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

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    chat = Chat(event, is_image_event=True)
    Bot(chat)
    del chat

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    chat = Chat(event, is_image_event=False)
    Bot(chat)
    del chat
