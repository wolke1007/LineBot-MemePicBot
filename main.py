# -*- coding: utf-8 -*-
import random
from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
import tempfile, os
from config import *
from imgur_auth import ImgurClient
import re
import requests
import base64
import json

app = Flask(__name__)
line_bot_api = LineBotApi(line_channel_access_token)
handler = WebhookHandler(line_channel_secret)
API_URL = 'https://api.imgur.com/'
MASHAPE_URL = 'https://imgur-apiv3.p.mashape.com/'
UserInfoDict = {}
PicNameDict = {}

# UserInfoDict  格式定為 { 'user_id': { 'pic_name': '圖片名稱', 'pic_content': 'binary content', 
#                       'pic_link': 'https://imgur.xxx.xxx', 'banned':False }}
# PicNameDict   格式定為 { 'pic_name' : 'pic_link' }

###################################################
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

def AddUserIdIfNotExist(user_id):
    print('enter AddUserIdIfNotExist')
    if user_id not in UserInfoDict.keys():
        new_dict = {user_id: {'pic_name': None, 'pic_content': None, 'pic_link': None, 'banned':False}}
        UserInfoDict.update(new_dict)
        return True

def isUserIdBanned(user_id):
    if UserInfoDict.get(user_id).get('banned'):
        return True
    else:
        return False

def isPicContentExist(user_id):
    print('enter isPicContentExist')
    if UserInfoDict.get(user_id).get('pic_content'):
        return True
    else:
        return False

def isFileNameExist(user_id):
    print('enter isFileNameExist')
    if UserInfoDict.get(user_id).get('pic_name'):
        return True
    else:
        return False
    
def SavePicContentToDict(user_id, group_id, message_id):
    print('enter SavePicContentToDict')
    message_content = line_bot_api.get_message_content(message_id)
    UserInfoDict[user_id]['pic_content'] = message_content
    to = group_id if group_id else user_id
    line_bot_api.push_message(
        to,
        TextSendMessage(text='已儲存圖片暫存檔, type(message_content.content): ' + str(type(message_content.content)) +
                            ', message_content.response: ' + str(message_content.response) +
                            ', message_content.content_type: ' + str(message_content.content_type)
                            )
    )
    return True

def UploadToImgur(user_id, group_id):
    print('enter UploadToImgur')
    Pic_Name = UserInfoDict.get(user_id).get('pic_name')
    try:
        binary_pic = UserInfoDict.get(user_id).get('pic_content')
        # print('type binary_pic: '+str(type(binary_pic)))
        # print('type binary_pic.content: '+str(type(binary_pic.content)))
        payload = base64.b64encode(binary_pic.content)
        ################################
        data = {
            'image': payload,
            'album': Album_ID,
            'name': Pic_Name,
            'title': Pic_Name,
            'description': 'Upload From MemePicLineBot'
        }
        # 這邊要考慮在 description 中加入 sha256 加密過的使用者 line user id 來達到嚇阻避免使用者濫用，濫用情況類似像是 PO 違法照片等等
        # 也要想方法公告表示不要將個人資料與非法照片上傳（類似裸照或是未成年照片等等，我不想被ＦＢＩ抓．．．）否則將依法究辦之類的
        InstanceClient = ImgurClient(client_id, client_secret, access_token, refresh_token)
        headers = InstanceClient.prepare_headers()
        response = requests.post('https://api.imgur.com/3/image', headers=headers, data=data)
        pic_link = json.loads(response.text)['data']['link']
        ########################################################################
        to = group_id if group_id else user_id
        line_bot_api.push_message(
            to,
            TextSendMessage(text='上傳至Imgur成功, pic link: '+str(pic_link))
            )
        # line_bot_api.push_message(
        #             to,
        #             ImageSendMessage(preview_image_url=pic_link,
        #                             original_content_url=pic_link)
        #         )
        return pic_link
    except Exception as e:
        print(e)
        to = group_id if group_id else user_id
        line_bot_api.push_message(
            to,
            TextSendMessage(text='上傳至Imgur失敗'))
        return None

def GetPicFromPicLink(user_id):
    pic_link = UserInfoDict[user_id]['pic_link']
    return pic_link

def CheckMsgContent(MsgContent):
    for PicName in PicNameDict.keys():
        if re.search(MsgContent, PicName):
            return PicNameDict.get(PicName)
    return False

# #################################################
#                收到圖片後邏輯
# #################################################
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id
    message_id = event.message.id
    try:
        group_id = event.source.group_id
    except AttributeError as e:
        group_id = None
        print("send from 1 to 1 chat room, so there's no group id")
    AddUserIdIfNotExist(user_id)
    # 檢查該 user 是否已經被 banned
    if isUserIdBanned(user_id):
        try:
            raise Exception('This user id' + str(user_id) + 'got banned, refuse to do anything!')
        except Exception:
            print('This user id' + str(user_id) + 'got banned, refuse to do anything!')
        return True

    SavePicContentToDict(user_id, group_id, message_id)

    if isFileNameExist(user_id):
        ''' 檔案名稱已取好了 '''
        print('name already exist, start to upload')
        pic_link = UploadToImgur(user_id, group_id)
        pic_name = UserInfoDict.get(user_id).get('pic_name')
        PicNameDict[pic_name] = pic_link
        print('set PicNameDict done')
        UserInfoDict[user_id]['pic_content'] = None
        print('empty pic_content done')
        UserInfoDict[user_id]['pic_name'] = None
        print('empty pic_name done')
    else:
        ''' 檔案名稱還沒取好 '''
        line_bot_api.push_message(
            to,
            TextSendMessage(text='檔案已存成暫存檔，請設定圖片名稱，範例: #圖片名稱#')
            )

# #################################################
#                   收到文字後邏輯
# #################################################
@handler.add(MessageEvent, message=TextMessage)    
def handle_text(event):
    user_id = event.source.user_id
    message_id = event.message.id
    try:
        group_id = event.source.group_id
    except AttributeError as e:
        group_id = None
        print("send from 1 to 1 chat room, so there's no group id")
    Line_Msg_Text = event.message.text
    AddUserIdIfNotExist(user_id)
    # 檢查該 user 是否已經被 banned
    if isUserIdBanned(user_id):
        try:
            raise Exception('This user id' + str(user_id) + 'got banned, refuse to do anything!')
        except Exception:
            print('This user id' + str(user_id) + 'got banned, refuse to do anything!')
        return True

    if isinstance(event.message, TextMessage):
        if event.message.text[0] == "#" and event.message.text[-1] == "#":
            print('enter event.message.text[0] == "#" and event.message.text[-1] == "#"') #debug
            # 因為會覆寫，所以直接再 Add 一次不用刪除
            UserInfoDict[user_id]['pic_name'] = Line_Msg_Text[1:-1]
            print('add to pic_name done')
            if isPicContentExist(user_id):
                pic_link = UploadToImgur(user_id, group_id)
                pic_name = UserInfoDict.get(user_id).get('pic_name')
                PicNameDict[pic_name] = pic_link
                print('set PicNameDict done')
                UserInfoDict[user_id]['pic_content'] = None
                print('empty pic_content done')
                UserInfoDict[user_id]['pic_name'] = None
                print('empty pic_name done')
            else:
                to = group_id if group_id else user_id
                line_bot_api.push_message(
                    to,
                    TextSendMessage(text='圖片名稱已設定完畢，請上傳圖片')
                )
        elif event.message.text == "--debug":
            print('event.message.text == "--debug"') #debug
            to = group_id if group_id else user_id
            line_bot_api.push_message(
                    to,
                    TextSendMessage(text='UserInfoDict = ' + str(UserInfoDict) + 'PicNameDict = ' + str(PicNameDict))
                )
        elif event.message.text == "--help":
            print('event.message.text == "--help"') #debug
            to = group_id if group_id else user_id
            line_bot_api.push_message(
                    to,
                    ImageSendMessage(preview_image_url='https://steemitimages.com/DQmPfGvYUqg9TUsaK8EUegqL2gVGR8FSS67FtYRs86UfUP1/help-and-support.png',
                                    original_content_url='https://steemitimages.com/DQmPfGvYUqg9TUsaK8EUegqL2gVGR8FSS67FtYRs86UfUP1/help-and-support.png')
                )
            line_bot_api.push_message(
                    to,
                    TextSendMessage(text='請使用 "#"+"圖片名稱"+"#" 來設定圖片名稱，範例: #圖片名稱#')
                )
        else:
            print('CheckMsgContent(event.message.text)') #debug
            PICLINK = CheckMsgContent(event.message.text)
            if PICLINK:
                to = group_id if group_id else user_id
                line_bot_api.push_message(
                        to,
                        ImageSendMessage(preview_image_url=PICLINK,
                                        original_content_url=PICLINK)
                    )
            PICLINK = None
            print('clean PICLINK')