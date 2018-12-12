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
import logging
import pymysql
from sqlalchemy import text
from sqlalchemy import create_engine


app = Flask(__name__)
line_bot_api = LineBotApi(line_channel_access_token)
handler = WebhookHandler(line_channel_secret)
API_URL = 'https://api.imgur.com/'
MASHAPE_URL = 'https://imgur-apiv3.p.mashape.com/'
################# System Dict 要再想要怎麼實作#################
System = {'talk_mode':True, 'retrieve_pic_mode':True, }

######### SQL 相關的 code #########
CONNECTION_NAME = getenv(
  'INSTANCE_CONNECTION_NAME',
  '<YOUR INSTANCE CONNECTION NAME>')
DB_USER = getenv('MYSQL_USER', '<YOUR DB USER>')
DB_PASSWORD = getenv('MYSQL_PASSWORD', '<YOUR DB PASSWORD>')
DB_NAME = getenv('MYSQL_DATABASE', '<YOUR DB NAME>')

user_info_connect = 'mysql+pymysql://root:'+DB_PASSWORD+'@/'+DB_NAME+'?unix_socket=/cloudsql/'+CONNECTION_NAME
# mysql+pymysql://<USER>:<PASSWORD>@/<DATABASE_NAME>?unix_socket=/cloudsql/<PUT-SQL-INSTANCE-CONNECTION-NAME-HERE>
engine = create_engine(user_info_connect)

def select_from_db(pre_sql, select_params_dict):
    bind_sql = text(pre_sql)
    with engine.connect() as conn:
        try:
            resproxy = conn.execute(bind_sql, select_params_dict)
            rows = resproxy.fetchall()
            ret = rows
            return ret
        except:
            return False

def insert_from_db(pre_sql, insert_params_dict):
    bind_sql = text(pre_sql)
    with engine.connect() as conn:
        try:
            resproxy = conn.execute(bind_sql, insert_params_dict)
            return True
        except:
            return False

def update_from_db(pre_sql, update_params_dict):
    bind_sql = text(pre_sql)
    with engine.connect() as conn:
        try:
            resproxy = conn.execute(bind_sql, update_params_dict)
            return True
        except:
            return False
######### SQL 相關的 code 結束 ########


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
    select_params_dict = {
                'user_id': user_id,
                }
    select_pre_sql = "SELECT user_id FROM user_info WHERE user_id = :user_id"
    res = select_from_db(select_pre_sql, select_params_dict)
    # 回傳值應為 list type 裡面包著 tuple，但有可能沒有值所以不指定取第一個
    if res:
        # user_id 存在，不做事
        return
    else:
        # user_id 不存在，加入
        insert_params_dict = {
                'user_id': user_id,
                'banned': 0,
                }
        insert_pre_sql = "INSERT INTO user_info (user_id, banned) VALUES (:user_id, :banned)"
        insert_from_db(insert_pre_sql, insert_params_dict)
        return True

def isUserIdBanned(user_id):
    logging.debug('enter isUserIdBanned')
    select_params_dict = {
                'user_id': user_id,
                }
    select_pre_sql = "SELECT banned FROM user_info WHERE user_id = :user_id"
    # 有設定圖片名稱，但是還沒上傳所以沒有 pic_link
    res = select_from_db(select_pre_sql, select_params_dict)
    # 回傳值應為 list type 裡面包著 tuple，預期只有一個同名的使用者且一定有使用者 id 存在不怕沒取到噴錯，故直接取第一個
    print('isUserIdBanned type res', type(res))
    if res[0][0] == False:
        # 沒有被 banned
        print('user_id not got banned')
        return False
    else:
        # 被 banned 的帳號
        print('user_id got banned', res[0][0])
        return True

def isFileNameExist(user_id, pic_name=True, checkrepeat=True):
    logging.debug('enter isFileNameExist')
    select_params_dict = {
                'user_id': user_id,
                'pic_name': pic_name,
                }
    if checkrepeat is True:
        select_pre_sql = "SELECT pic_name FROM pic_info WHERE pic_name = :pic_name"
    else:
        select_pre_sql = "SELECT pic_name FROM pic_info WHERE pic_link IS NULL"
    # 有設定圖片名稱，但是還沒上傳所以沒有 pic_link
    res = select_from_db(select_pre_sql, select_params_dict)
    if res:
        return True
    else:
        return False

def UploadToImgur(user_id, group_id, binary_pic):
    logging.debug('enter UploadToImgur')
    select_params_dict = {
                'user_id': user_id,
                }
    # 名字設定好但還沒有 pic_link 的且 user_id 符合的就是準備要上傳的
    select_pre_sql = "SELECT pic_name FROM pic_info WHERE pic_link IS NULL AND user_id = :user_id"
    # 回傳為 list type 裡面包著 tuple 預期一定會拿到 pic_name 所以直接取第一個不怕噴錯
    Pic_Name = select_from_db(select_pre_sql, select_params_dict)[0][0]
    try:
        logging.debug('type binary_pic: '+str(type(binary_pic)))
        logging.debug('type binary_pic.content: '+str(dir(binary_pic)))
        payload = base64.b64encode(binary_pic)
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
        reply_msg = '上傳成功'
        return pic_link, reply_msg
    except Exception as e:
        logging.debug(e)
        reply_msg = '上傳失敗，請聯絡管理員'
        return '', reply_msg

def CheckMsgContent(MsgContent):
    MsgContent = MsgContent.lower()
    select_params_dict = {
        'pic_name': MsgContent,
        }
    select_pre_sql = "SELECT pic_link FROM pic_info WHERE pic_name = :pic_name"
    ########## 這邊有效能問題需要解決，目前是每一句對話都去掃描全部的 DB ############
    res = select_from_db(select_pre_sql, select_params_dict)
    if res:
        # 回傳 pic
        PICLINK = res[0][0]
        return PICLINK
    else:
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
        return
    
    if isFileNameExist(user_id, checkrepeat=False):
        ''' 檔案名稱已取好了 '''
        logging.debug('name already exist, start to upload')
        print('dir line_bot_api.get_message_content(event): ', dir(line_bot_api.get_message_content(message_id).content))
        print('type line_bot_api.get_message_content(event): ', type(line_bot_api.get_message_content(message_id).content))
        binary_pic = line_bot_api.get_message_content(message_id).content
        pic_link, reply_msg = UploadToImgur(user_id, group_id, binary_pic)
        update_params_dict = {
            'user_id': user_id,
            'pic_link': pic_link,
            }
        # 名字設定好但還沒有 pic_link 的且 user_id 符合的就是剛上傳好的
        update_pre_sql = "UPDATE pic_info SET pic_link=:pic_link WHERE user_id = :user_id AND pic_link IS NULL"
        update_from_db(update_pre_sql, update_params_dict)
        LineReplyMsg(event.reply_token, reply_msg, content_type='text')

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
        return
    
    Line_Msg_Text = event.message.text
    if isinstance(event.message, TextMessage):
        if event.message.text[0] == "#" and event.message.text[-1] == "#":
            logging.debug('enter event.message.text[0] == "#" and event.message.text[-1] == "#"') #debug
            # 因為會覆寫，所以直接再 Add 一次不用刪除，且統一用小寫儲存
            # 圖片名稱長度在此設定門檻，目前設定為４~15 個字
            pic_name = Line_Msg_Text[1:-1].lower()
            if len(pic_name) >= 4 and len(pic_name) <=15 :
                if isFileNameExist(user_id, pic_name=pic_name, checkrepeat=True):
                    # 如果圖片重複了，對 user_id pic_link 欄位進行 update
                    print('圖片已經存在，更新 user_id pic_link')
                    update_params_dict = {
                        'user_id': user_id,
                        'pic_name': pic_name,
                        }
                    update_pre_sql = "UPDATE pic_info SET user_id=:user_id, pic_link=NULL WHERE pic_name = :pic_name"
                    res = update_from_db(update_pre_sql, update_params_dict)
                    print('user_id pic_link 已經淨空，準備接收新圖片')
                else:
                    # 如果沒重複直接 insert
                    print('新增 user_id pic_name')
                    insert_params_dict = {
                    'user_id': user_id,
                    'pic_name': pic_name,
                    }
                    insert_pre_sql = "INSERT INTO pic_info (user_id, pic_name) values (:user_id, :pic_name)"
                    res = insert_from_db(insert_pre_sql, insert_params_dict)
                    print('user_id pic_name 已經新增，準備接收新圖片')
                if res is True:
                    LineReplyMsg(event.reply_token, '圖片名稱已設定完畢，請上傳圖片', content_type='text')
                else:
                    LineReplyMsg(event.reply_token, 'Database 寫檔失敗！請聯絡管理員', content_type='text')
            else:
                LineReplyMsg(event.reply_token, '圖片名稱長度需介於 4~15 個字（中英文或數字皆可)', content_type='text')
                return

            logging.debug('add to pic_name done')
        # debug mode 之後要拔掉，或是要經過驗證，否則 user id 會輕易曝光
        # 或是看看有沒有辦法只回覆擁有者
        # 這邊之後要改寫成一個獨立的檔案，並只 return 要回傳的字串，這邊則是負責幫忙送出
        elif event.message.text[0:7] == "--debug":
            logging.debug('event.message.text == "--debug"') #debug
            # --debug 是 [7:]，從 8 開始是因為預期會有空白， e.g. '--debug -q'
            print('enter debug')
            command = event.message.text[8:]
            print('command: ', command)
            if not command :
                select_params_dict = {}
                res = select_from_db("SELECT user_id FROM pic_info", select_params_dict)
                LinePushTextMsg(user_id, res)
                res = select_from_db("SELECT pic_name FROM pic_info", select_params_dict)
                LinePushTextMsg(user_id, res)
                res = select_from_db("SELECT created_time FROM pic_info", select_params_dict)
                LinePushTextMsg(user_id, res)

            elif command is 'help' :
                LinePushTextMsg(user_id, '\
                        -q : quiet mode, for not talk back.\n \
                        ')
            elif command[5:] is '-q 0' :
                System['talk_mode'] = False
                LinePushTextMsg(user_id, 'set talk_mode to Quiet Mode')

            # 這邊要改寫成判斷最後一個字元來決定要做什麼事
            elif command[5:] is '-q 1' :
                System['talk_mode'] = True
                LinePushTextMsg(user_id, 'set talk_mode to Quiet Mode')

        elif event.message.text == "--help":
            logging.debug('event.message.text == "--help"') #debug
            LineReplyMsg(event.reply_token, \
# line 手機版莫約 15 個中文字寬度就會換行
'''
貼心提醒您請勿洩漏個資
嚴 禁 上 傳 色 情 圖 片
(作者: 我不想被 Imgur banned 拜託配合了ＱＡＱ
使用教學：
1. 先設定圖片名稱完後再上傳圖片
2. 使用 #圖片名稱# 的方式設定圖片名稱，範例: #大什麼大 人什麼人#
3. 設定同圖片名稱會蓋掉前面上傳的
''', content_type='text')

        elif event.message.text == "--mode":
            logging.debug('event.message.text == "--mode"') #debug
            LineReplyMsg(event.reply_token, '當前模式為: ' + System.get('mode'), content_type='text')

        
        elif event.message.text == "sql-test insert user_id":

            # select_params_dict = {
            #     'user_id': 'test_user_id',
            #     'pic_name': 'test_pic_name',
            #     'pic_link': 'test_pic_link',
            #     }
            # select_pre_sql = "SELECT user_id FROM pic_info WHERE user_id = :user_id"
            # select_from_db(select_pre_sql, select_params_dict)
            
            # insert_params_dict = {
            #     'user_id': 'test_user_id',
            #     'pic_name': 'test_pic_name',
            #     'pic_link': 'test_pic_link',
            #     }
            # insert_pre_sql = "INSERT INTO pic_info (user_id, pic_name, pic_link) values (:user_id, :pic_name, :pic_link)"
            # insert_from_db(insert_pre_sql, insert_params_dict)

            # update_params_dict = {
            #     'user_id': 'test_user_id',
            #     'pic_name': 'test_pic_name',
            #     'pic_link': 'test_pic_link',
            #     }
            # update_pre_sql = "UPDATE pic_info SET pic_name=123, pic_link='123' WHERE user_id = :user_id"
            # update_from_db(update_pre_sql, update_params_dict)

            select_params_dict = {
                'state': 'Texas',
                }
            select_pre_sql = "SELECT state FROM census WHERE state = :state"
            select_from_db(select_pre_sql, select_params_dict)

            logging.info('sqlalchemy test pass')
            pass

        else:
            # 根據模式決定要不要回話
            if System.get('talk_mode') is False: return          
            logging.debug('CheckMsgContent(event.message.text)') #debug
            PICLINK = CheckMsgContent(event.message.text)
            if PICLINK:
                print('PICLINK', PICLINK)
                LineReplyMsg(event.reply_token, PICLINK, content_type='image')
            PICLINK = None
            logging.debug('clean PICLINK')






# SQL 參考：
# 1. https://www.jianshu.com/p/e6bba189fcbd
# 2. https://blog.csdn.net/slvher/article/details/47154363
