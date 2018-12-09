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
from os import getenv
import pymysql
from pymysql.err import OperationalError
import logging

app = Flask(__name__)
line_bot_api = LineBotApi(line_channel_access_token)
handler = WebhookHandler(line_channel_secret)
API_URL = 'https://api.imgur.com/'
MASHAPE_URL = 'https://imgur-apiv3.p.mashape.com/'
System = {'talk_mode':True, 'retrieve_pic_mode':True, }
UserInfoDict = {}
PicNameDict = {}

######### SQL 相關的 code #########
CONNECTION_NAME = getenv(
  'INSTANCE_CONNECTION_NAME',
  '<YOUR INSTANCE CONNECTION NAME>')
DB_USER = getenv('MYSQL_USER', '<YOUR DB USER>')
DB_PASSWORD = getenv('MYSQL_PASSWORD', '<YOUR DB PASSWORD>')
DB_NAME = getenv('MYSQL_DATABASE', '<YOUR DB NAME>')

mysql_config = {
  'user': DB_USER,
  'password': DB_PASSWORD,
  'db': DB_NAME,
  'charset': 'utf8mb4',
  'cursorclass': pymysql.cursors.DictCursor,
  'autocommit': True
}

# Create SQL connection globally to enable reuse
# PyMySQL does not include support for connection pooling
mysql_conn = None

def __get_cursor():
    """
    Helper function to get a cursor
      PyMySQL does NOT automatically reconnect,
      so we must reconnect explicitly using ping()
    """
    try:
        return mysql_conn.cursor()
    except OperationalError:
        mysql_conn.ping(reconnect=True)
        return mysql_conn.cursor()


def mysql_demo(request):
    global mysql_conn

    # Initialize connections lazily, in case SQL access isn't needed for this
    # GCF instance. Doing so minimizes the number of active SQL connections,
    # which helps keep your GCF instances under SQL connection limits.
    if not mysql_conn:
        try:
            mysql_conn = pymysql.connect(**mysql_config)
        except OperationalError:
            # If production settings fail, use local development ones
            mysql_config['unix_socket'] = f'/cloudsql/{CONNECTION_NAME}'
            mysql_conn = pymysql.connect(**mysql_config)

    # Remember to close SQL resources declared while running this function.
    # Keep any declared in global scope (e.g. mysql_conn) for later reuse.
    with __get_cursor() as cursor:
        cursor.execute('SELECT NOW() as now')
        results = cursor.fetchone()
        return str(results['now'])


######### SQL 相關的 code #########

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
    logging.debug('enter AddUserIdIfNotExist')
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
    logging.debug('enter isPicContentExist')
    if UserInfoDict.get(user_id).get('pic_content'):
        return True
    else:
        return False

def isFileNameExist(user_id):
    logging.debug('enter isFileNameExist')
    if UserInfoDict.get(user_id).get('pic_name'):
        return True
    else:
        return False
    
def SavePicContentToDict(user_id, group_id, message_id):
    logging.debug('enter SavePicContentToDict')
    message_content = line_bot_api.get_message_content(message_id)
    UserInfoDict[user_id]['pic_content'] = message_content
    return True

def UploadToImgur(user_id, group_id):
    logging.debug('enter UploadToImgur')
    Pic_Name = UserInfoDict.get(user_id).get('pic_name')
    try:
        binary_pic = UserInfoDict.get(user_id).get('pic_content')
        logging.debug('type binary_pic: '+str(type(binary_pic)))
        logging.debug('type binary_pic.content: '+str(type(binary_pic.content)))
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
        reply_msg = '上傳至Imgur成功'
        return pic_link, reply_msg
    except Exception as e:
        logging.debug(e)
        reply_msg = '上傳至Imgur失敗'
        return '', reply_msg

def GetPicFromPicLink(user_id):
    pic_link = UserInfoDict[user_id]['pic_link']
    return pic_link

def CheckMsgContent(MsgContent):
    MsgContent = MsgContent.lower()
    for PicName in PicNameDict.keys():
        if re.search(PicName, MsgContent):
            return PicNameDict.get(PicName)
    return False

def LineReplyMsg(to, content, content_type):
    if content_type is 'text':
        line_bot_api.reply_message(
            to,
            TextSendMessage(text=content))
    elif content_type is 'image':
        line_bot_api.reply_message(
            to,
            ImageSendMessage(preview_image_url=content,
                            original_content_url=content))

def LinePushTextMsg(to, content):
    line_bot_api.push_message(
            to,
            TextSendMessage(text=content))
# #################################################
#                收到圖片後邏輯                     #
# ################################################# 
# 研究後發現，如果要顧及收到圖片後再上傳這件事情，那將遇到幾個難題
# 首先:
# 1. 因為線上會起多個 process 所以將圖片暫存檔記在 memory 有機會是另一個 process 去檢查結果發現沒有圖片 
# 2. 而之後有考慮用 pickle 的方式儲存檔案，但 Google Cloud Function 不支援寫檔案的動作所以無法
# 接下來我們有其他作法可以考慮:
# 1. 先存圖片到 DB 再上傳
#    但那將會增加 DB Server 傳輸負擔跟流量成本
# 2. 只要收到圖片一律上傳，如果仍未命名但又有收到圖片，就刪除前一張後再上傳，直到有命名則修改最後一張上傳圖片的名稱為正式名稱
#    但這會增加上傳的成本，依據 Imgur 免費的流量只能上傳 10,000 張圖片每月，就算花 25 鎂也是 60,000 每月，並不能這樣玩
# 最後決定，只能確認使用者有先命名完才做上傳動作，確保每一次有確定要上傳才做
# 與此同時，有考慮每個人是不是要設定 quota 來限制是不是一天只能上傳幾張圖片
# 此部分可能可以在未來自己架設圖片 server 來解決這個問題
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id
    message_id = event.message.id
    try:
        group_id = event.source.group_id
    except AttributeError as e:
        group_id = None
        logging.debug("send from 1 to 1 chat room, so there's no group id")
    # 將 user 建檔管理
    AddUserIdIfNotExist(user_id)
    # 檢查該 user 是否已經被 banned
    if isUserIdBanned(user_id):
        try:
            raise Exception('This user id' + str(user_id) + 'got banned, refuse to do anything!')
        except Exception:
            logging.warning('This user id' + str(user_id) + 'got banned, refuse to do anything!')
        return True
    
    # 直接再儲存一次，已經存在的話就覆蓋過去
    SavePicContentToDict(user_id, group_id, message_id)
    logging.debug('已儲存圖片暫存檔')
    
    if isFileNameExist(user_id):
        ''' 檔案名稱已取好了 '''
        logging.debug('name already exist, start to upload')
        pic_link, reply_msg = UploadToImgur(user_id, group_id)
        pic_name = UserInfoDict.get(user_id).get('pic_name')
        PicNameDict[pic_name] = pic_link
        logging.debug('set PicNameDict done')
        UserInfoDict[user_id]['pic_content'] = None
        logging.debug('empty pic_content done')
        UserInfoDict[user_id]['pic_name'] = None
        logging.debug('empty pic_name done')
        LineReplyMsg(event.reply_token, reply_msg, content_type='text')
    else:
        ''' 檔案名稱還沒取好 '''
        LineReplyMsg(event.reply_token, '檔案已存成暫存檔，請設定圖片名稱，範例: #圖片名稱#', content_type='text')

# #################################################
#                   收到文字後邏輯                  #
# #################################################
@handler.add(MessageEvent, message=TextMessage)    
def handle_text(event):
    user_id = event.source.user_id
    message_id = event.message.id
    try:
        group_id = event.source.group_id
    except AttributeError as e:
        group_id = None
        logging.debug("send from 1 to 1 chat room, so there's no group id")
    # 將 user 建檔管理
    AddUserIdIfNotExist(user_id)
    # 檢查該 user 是否已經被 banned
    if isUserIdBanned(user_id):
        try:
            raise Exception('This user id' + str(user_id) + 'got banned, refuse to do anything!')
        except Exception:
            logging.warning('This user id' + str(user_id) + 'got banned, refuse to do anything!')
        return True
    
    Line_Msg_Text = event.message.text
    if isinstance(event.message, TextMessage):
        if event.message.text[0] == "#" and event.message.text[-1] == "#":
            logging.debug('enter event.message.text[0] == "#" and event.message.text[-1] == "#"') #debug
            # 因為會覆寫，所以直接再 Add 一次不用刪除，且統一用小寫儲存
            # 圖片名稱長度在此設定門檻，目前設定為４~10 個字
            pic_name = Line_Msg_Text[1:-1].lower()
            if len(pic_name) >= 4 and len(pic_name) <=10 :
                UserInfoDict[user_id]['pic_name'] = pic_name
            else:
                LineReplyMsg(event.reply_token, '圖片名稱長度需介於 4~10 個字（中英文或數字皆可)', content_type='text')
                return

            logging.debug('add to pic_name done')
            if isPicContentExist(user_id):
                pic_link = UploadToImgur(user_id, group_id)
                pic_name = UserInfoDict.get(user_id).get('pic_name')
                PicNameDict[pic_name] = pic_link
                logging.debug('set PicNameDict done')
                UserInfoDict[user_id]['pic_content'] = None
                logging.debug('empty pic_content done')
                UserInfoDict[user_id]['pic_name'] = None
                logging.debug('empty pic_name done')
            else:
                # to = group_id if group_id else user_id
                LineReplyMsg(event.reply_token, '圖片名稱已設定完畢，請上傳圖片', content_type='text')
        # debug mode 之後要拔掉，或是要經過驗證，否則 user id 會輕易曝光
        # 或是看看有沒有辦法只回覆擁有者
        # 這邊之後要改寫成一個獨立的檔案，並只 return 要回傳的字串，這邊則是負責幫忙送出
        elif event.message.text[0:7] == "--debug":
            logging.debug('event.message.text == "--debug"') #debug
            # --debug 是 [7:]，從 8 開始是因為預期會有空白， e.g. '--debug -q'
            command = event.message.text[8:]
            to = group_id if group_id else user_id
            if not command :
                LinePushTextMsg(to, 'UserInfoDict = ' + str(UserInfoDict) + 'PicNameDict = ' + str(PicNameDict)
                        + 'to: ' + str(to))
            elif command is 'help' :
                LinePushTextMsg(to, '\
                        -q : quiet mode, for not talk back.\n \
                        -q : quiet mode, for not talk back.\n \
                        ')
            elif command[5:] is '-q 0' :
                System['talk_mode'] = False
                LinePushTextMsg(to, 'set talk_mode to Quiet Mode')

            # 這邊要改寫成判斷最後一個字元來決定要做什麼事
            elif command[5:] is '-q 1' :
                System['talk_mode'] = True
                LinePushTextMsg(to, 'set talk_mode to Quiet Mode')

        elif event.message.text == "--help":
            logging.debug('event.message.text == "--help"') #debug
            LineReplyMsg(event.reply_token, '請使用 "#"+"圖片名稱"+"#" 來設定圖片名稱，範例: #圖片名稱', content_type='text')

        elif event.message.text == "--mode":
            logging.debug('event.message.text == "--mode"') #debug
            LineReplyMsg(event.reply_token, '當前模式為: ' + System.get('mode'), content_type='text')

        
        elif event.message.text == "sql-test insert user_id":
            with __get_cursor() as cursor:
                insert = ("INSERT INTO user_info (user_id, banned, account_created_time) VALUES (%s, %s, CURDATE()")
                data = ('test_123',False)
                cursor.executemany(insert, data)
                connection.commit()


        else:
            # 根據模式決定要不要回話
            if System.get('talk_mode') is False: return          
            logging.debug('CheckMsgContent(event.message.text)') #debug
            PICLINK = CheckMsgContent(event.message.text)
            if PICLINK:
                LineReplyMsg(event.reply_token, PICLINK, content_type='image')
            PICLINK = None
            logging.debug('clean PICLINK')
