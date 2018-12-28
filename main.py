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
from base64 import b64encode
import json
from os import getenv
import logging
import pymysql
from sqlalchemy import text
from sqlalchemy import create_engine
# --list function 用的，拉出來看能不能加速那部分的 function 否則用到才 import 容易太久導致 reply token timeout 
# from pandas import DataFrame
# from numpy import array
# from matplotlib.pyplot import subplots
# from io import BytesIO
# from six import iteritems
# from PIL import Image
# from matplotlib.font_manager import FontProperties

app = Flask(__name__)
line_bot_api = LineBotApi(line_channel_access_token)
handler = WebhookHandler(line_channel_secret)
API_URL = 'https://api.imgur.com/'
MASHAPE_URL = 'https://imgur-apiv3.p.mashape.com/'
################# System Dict 要再想要怎麼實作#################
System = {'talk_mode':True, 'retrieve_pic_mode':True, }
# 設定圖片名稱的字數的長度在此控制
pic_name_low_limit = 2
pic_name_high_limit = 15

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
    print('enter AddUserIdIfNotExist')
    select_params_dict = {
                'user_id': user_id,
                }
    select_pre_sql = "SELECT user_id FROM user_info WHERE user_id=:user_id"
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
    print('enter isUserIdBanned')
    select_params_dict = {
                'user_id': user_id,
                }
    select_pre_sql = "SELECT banned FROM user_info WHERE user_id=:user_id"
    # 有設定圖片名稱，但是還沒上傳所以沒有 pic_link
    res = select_from_db(select_pre_sql, select_params_dict)
    # 回傳值應為 list type 裡面包著 tuple，預期只有一個同名的使用者且一定有使用者 id 存在不怕沒取到噴錯，故直接取第一個
    if res[0][0] == False:
        # 沒有被 banned
        print('user_id not got banned')
        return False
    else:
        # 被 banned 的帳號
        print('user_id got banned', res[0][0])
        return True

def isFileNameExist(pic_name, group_id):
    print('enter isFileNameExist')
    if not pic_name:
        return False
    select_params_dict = {
                'pic_name': pic_name,
                'group_id': group_id,
                }
    select_pre_sql = "SELECT pic_name FROM pic_info WHERE \
                      pic_name=:pic_name AND group_id=:group_id"
    # 有設定圖片名稱，但是還沒上傳所以沒有 pic_link
    res = select_from_db(select_pre_sql, select_params_dict)
    return True if res else False

def UploadToImgur(Pic_Name, binary_pic=None, url=None):
    print('enter UploadToImgur')
    try:
        payload = base64.b64encode(binary_pic) if binary_pic else url
        print('type(payload)', type(payload))
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
        print('UploadToImgur Exception e:', e)
        reply_msg = '上傳失敗，請聯絡管理員'
        return '', reply_msg

def CheckMsgContent(MsgContent, trigger_chat, group_id):
    print('CheckMsgContent, MsgContent, trigger_chat, group_id',MsgContent, trigger_chat, group_id)
    select_pre_sql = "SELECT pic_name, group_id FROM pic_info"
    ########## 這邊有效能問題需要解決 ##########
    # 目前是每一句對話都去抓全部的 DB 回來，然後丟進 for loop 掃描全部的內容
    # 1. DB server 的運算部分目前已知要錢，所以不要讓它算，要靠 Cloud Function 那邊的資源
    # 2. 所以整個抓回來再算是一種方法，但需要思考能不能不要每次都跟 DB 拿，而是哪邊有 server cache 之類的
    all_picname_in_db = select_from_db(select_pre_sql, select_params_dict={})
    print('all_picname_in_db', all_picname_in_db)
    match_list = []
    # 收到的格式為:  [('1','C123abc'), ('ABC','C456def')]
    if group_id:
        for pic_name in all_picname_in_db:
            # 到這邊變成 ('ABC','C123abc') 這樣，[0] 是 pic_name，[1] 是 group_id
            # group_id 有指定的話則要符合條件的才會 pass 到後面
            if group_id == pic_name[1]:
                pic_name = pic_name[0]
                # 這邊在解決如果 test 與 test2 同時存在，那 test2 將永遠不會被匹配到的問題，預期要取匹配到字數最長的
                match = re.search(str(pic_name), MsgContent, re.IGNORECASE)
                if match:
                    match_list.append(pic_name)
    else:
        for pic_name in all_picname_in_db:
            # 到這邊變成 ('ABC','C123abc') 這樣，[0] 是 pic_name，[1] 是 group_id
            # group_id 有指定的話則要符合條件的才會 pass 到後面
            pic_name = pic_name[0]
            # 這邊在解決如果 test 與 test2 同時存在，那 test2 將永遠不會被匹配到的問題，預期要取匹配到字數最長的
            match = re.search(str(pic_name), MsgContent, re.IGNORECASE)
            if match:
                match_list.append(pic_name)
    # 先確認 match_list 有沒有東西
    print('match_list', match_list)
    if match_list:        
        # key 這邊解決了如果不同名字，會依照字串長度排序
        match_list.sort(key=lambda x: len(x))
        # 排序後取 match 字數最多的也就是右邊一個
        pic_name = match_list[-1]
        # 如果圖片名稱小於設定的字數，那就回沒匹配到
        if len(pic_name) >= trigger_chat:
            group_id = group_id if group_id else 'NULL'
            if group_id is not 'NULL':
                select_pre_sql = "SELECT pic_link FROM pic_info WHERE pic_name=:pic_name and group_id=:group_id"
                res = select_from_db(select_pre_sql, select_params_dict={'pic_name': pic_name, 'group_id': group_id})
                print('CheckMsgContent group_id res:', group_id, res)
                return res[0][0] if res else False
            else:
                # 若 chat_mode = 1，group_id 會設定為 None 則邏輯會走到這裡，select 的時候就不能把 group_id 丟進去
                select_pre_sql = "SELECT pic_link FROM pic_info WHERE pic_name=:pic_name"
                res = select_from_db(select_pre_sql, select_params_dict={'pic_name': pic_name})
                from random import Random
                random_index = Random()
                random_index = random_index.choice(range(len(res)))
                print('CheckMsgContent group_id res random_index res:', group_id, random_index, res)
                return res[random_index][0] if res else False
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
# ~~~~~~先講結論~~~~~ 最後決定，只能確認使用者有先命名完才做上傳動作，確保每一次有確定要上傳才做
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
        group_id = 'NULL'
        print("send from 1 to 1 chat room, so there's no group id")
    # 將 user 建檔管理
    AddUserIdIfNotExist(user_id)
    # 檢查該 user 是否已經被 banned
    if isUserIdBanned(user_id):
        try:
            raise Exception('This user id' + str(user_id) + 'got banned, refuse to do anything!')
        except Exception:
            logging.warning('This user id' + str(user_id) + 'got banned, refuse to do anything!')
        return
    select_params_dict = {
        'user_id': user_id,
        'group_id': group_id,
    }
    # 名字設定好但還沒有 pic_link 的且 user_id 符合的就是準備要上傳的
    select_pre_sql = "SELECT pic_name FROM pic_info WHERE \
                        pic_link IS NULL AND user_id=:user_id AND group_id=:group_id"
    # 回傳為 list type 裡面包著 tuple 預期一定會拿到 pic_name 所以直接取第一個不怕噴錯
    Pic_Name = select_from_db(select_pre_sql, select_params_dict)
    Pic_Name = Pic_Name[0][0] if Pic_Name else None

    if isFileNameExist(Pic_Name, group_id):
        print('name already exist, start to upload') 
        binary_pic = line_bot_api.get_message_content(message_id).content
        print('type(binary_pic)', type(binary_pic))
        pic_link, reply_msg = UploadToImgur(Pic_Name, binary_pic=binary_pic)
        update_params_dict = {
            'user_id': user_id,
            'pic_link': pic_link,
            'group_id': group_id,
            }
        # 名字設定好但還沒有 pic_link 的且 user_id 符合的就是剛上傳好的
        update_pre_sql = "UPDATE pic_info SET pic_link=:pic_link, group_id=:group_id WHERE \
                          user_id=:user_id AND pic_link IS NULL"
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
        print('group_id:', group_id)
    except AttributeError as e:
        group_id = 'NULL'
        print("send from 1 to 1 chat room, so there's no group id")
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
            print('enter event.message.text[0] == "#" and event.message.text[-1] == "#"') #debug
            # 因為會覆寫，所以直接再 Add 一次不用刪除，且統一用小寫儲存
            # 圖片名稱長度在此設定門檻，目前設定為 3~15 個字
            pic_name = Line_Msg_Text[1:-1].lower()
            if len(pic_name) >= pic_name_low_limit and len(pic_name) <= pic_name_high_limit :
                if isFileNameExist(pic_name, group_id):
                    # 如果圖片重複了，對 user_id pic_link 欄位進行 update
                    print('圖片已經存在，更新 user_id pic_link')
                    update_params_dict = {
                        'user_id': user_id,
                        'pic_name': pic_name,
                        'group_id': group_id,
                        }
                    update_pre_sql = "UPDATE pic_info SET user_id=:user_id, pic_link=NULL \
                                      WHERE pic_name=:pic_name AND group_id=:group_id"
                    res = update_from_db(update_pre_sql, update_params_dict)
                    select_params_dict = {} #debug
                    debug_res = select_from_db("SELECT pic_name, pic_link FROM pic_info", select_params_dict) #debug
                    print('debug_res1: ',debug_res)
                    print('user_id pic_link 已經淨空，準備接收新圖片')
                else:
                    # 如果沒重複直接 insert
                    print('新增 user_id pic_name')
                    insert_params_dict = {
                    'user_id': user_id,
                    'pic_name': pic_name,
                    'group_id': group_id
                    }
                    insert_pre_sql = "INSERT INTO pic_info (user_id, pic_name, group_id) \
                                      values (:user_id, :pic_name, :group_id)"
                    res = insert_from_db(insert_pre_sql, insert_params_dict)
                    select_params_dict = {} #debug
                    debug_res = select_from_db("SELECT pic_name, pic_link FROM pic_info", select_params_dict) #debug
                    print('debug_res2: ',debug_res)
                    print('user_id pic_name 已經新增，準備接收新圖片')
                if res is True:
                    LineReplyMsg(event.reply_token, '圖片名稱已設定完畢，請上傳圖片', content_type='text')
                else:
                    LineReplyMsg(event.reply_token, 'Database 寫檔失敗！請聯絡管理員', content_type='text')
            else:
                LineReplyMsg(event.reply_token, '圖片名稱長度需介於 3~10 個字（中英文或數字皆可)', content_type='text')
                return

            print('add to pic_name done')

        elif event.message.text[:4] == "http" and (event.message.text[-4:] == ".jpg" \
                                               or event.message.text[-4:] == ".png" \
                                               or event.message.text[-4:] == ".gif") :
            select_params_dict = {
            'user_id': user_id,
            'group_id': group_id,
            }
            # 名字設定好但還沒有 pic_link 的就是準備要上傳的 
            # (只抓 user_id 符合的是為了避免設定名字後別人幫你上傳圖片的問題)
            select_pre_sql = "SELECT pic_name FROM pic_info WHERE \
                                pic_link IS NULL AND user_id=:user_id AND group_id=:group_id"
            # 回傳為 list type 裡面包著 tuple 預期一定會拿到 pic_name 所以直接取第一個不怕噴錯
            Pic_Name = select_from_db(select_pre_sql, select_params_dict)
            Pic_Name = Pic_Name[0][0] if Pic_Name else None

            if isFileNameExist(Pic_Name, group_id):
                print('name already exist, start to upload') 
                pic_link, reply_msg = UploadToImgur(Pic_Name, url=event.message.text)
                update_params_dict = {
                    'user_id': user_id,
                    'pic_link': pic_link,
                    'group_id': group_id,
                    }
                # 名字設定好但還沒有 pic_link 的且 user_id 符合的就是剛上傳好的
                update_pre_sql = "UPDATE pic_info SET pic_link=:pic_link, group_id=:group_id WHERE \
                                user_id=:user_id AND pic_link IS NULL"
                update_from_db(update_pre_sql, update_params_dict)
                LineReplyMsg(event.reply_token, reply_msg, content_type='text')

        elif event.message.text == "--help" or event.message.text == "-h" :
            print('event.message.text == "--help or "-h"') #debug
            LineReplyMsg(event.reply_token, \
# line 手機版莫約 15 個中文字寬度就會換行
'''
貼心提醒您請勿洩漏個資
嚴 禁 上 傳 色 情 圖 片
(作者: 我不想被 Imgur banned 拜託配合了ＱＡＱ
使用教學：
step 1. 設定圖片名稱，例如 #我是帥哥#
step 2. 上傳圖片，系統會回傳上傳成功
step 3. 聊天時提到設定的圖片名稱便會觸發貼圖

設定教學：
--mode chat_mode 0~2
0 = 不回圖
1 = 隨機回所有群組創的圖(預設)
2 = 只回該群組上傳的圖

--mode trigger_chat 2~15
設定在此群組裡超過幾字才回話，可以設為 2~15 

備註:
1. 圖片字數有限制，空白或是特殊符號皆算數
2. 設定同圖片名稱則會蓋掉前面上傳的
3. 若上傳URL則必須為 http 開頭 .jpg .gif .png 結尾
(目前尚未實作完成)
4. 建議在 Line 設定將「自動下載照片」取消打勾
設定 > 照片。影片 > 自動下載照片
5. 如果設定多次名字再上傳圖片，則是多個關鍵字對應同一張圖片
6. --list 可以讓 BOT 回你現有圖片名稱的表格
''', content_type='text')

        elif event.message.text[:6] == "--mode" and group_id :
            print('event.message.text == "--mode"') #debug
            # --mode trigger_chat 1
            if event.message.text[7:-2] == "trigger_chat":
                try:
                    mode = int(event.message.text[-2:].strip(' '))
                except:
                    LineReplyMsg(event.reply_token, 'trigger_chat 後需設定介於 2~15 的數字，如 --mode trigger_chat 15', content_type='text')
                    return
                # 不允許使用者設置低於 2 或是大於 15 個字元
                if mode < 2 or mode > 15:
                    LineReplyMsg(event.reply_token, 'trigger_chat 後需設定介於 2~15 的數字，如 --mode trigger_chat 15', content_type='text')
                    return
                update_params_dict = {
                'group_id': group_id,
                'trigger_chat': mode,
                }
                update_pre_sql = "UPDATE system SET trigger_chat=:trigger_chat \
                                  WHERE group_id=:group_id"
                update_from_db(update_pre_sql, update_params_dict)
                LineReplyMsg(event.reply_token, '更改 trigger_chat 為 '+str(mode), content_type='text')
            # --mode chat_mode 1
            elif event.message.text[7:-2] == "chat_mode" and group_id :
                try:
                    mode = int(event.message.text[-1])
                except:
                    LineReplyMsg(event.reply_token, 'chat_mode 後需設定介於 0~2 的數字，如 --mode chat_mode 2', content_type='text')
                    return
                update_params_dict = {
                'group_id': group_id,
                'chat_mode': mode,
                }
                update_pre_sql = "UPDATE system SET chat_mode=:chat_mode \
                                WHERE group_id=:group_id"
                update_from_db(update_pre_sql, update_params_dict)
                LineReplyMsg(event.reply_token, '更改 chat_mode 為 '+str(mode), content_type='text')
            else:
                select_pre_sql = "SELECT * FROM system WHERE group_id = :group_id"
                SystemConfig = select_from_db(select_pre_sql, select_params_dict={'group_id': group_id})
                if SystemConfig:
                    group_id_list = [i[0] for i in SystemConfig]
                    index = group_id_list.index(group_id)
                    # SystemConfig[index] 會回傳一個 tuple 類似像 ('Cxxxxxx', 1, 1, 3)
                    # 從左至右分別對應: group_id,	chat_mode, retrieve_pic_mode, trigger_chat
                    #                        其中 chat_mode 的設定：0 = 不回圖
                    #                                             1 = 隨機回所有 group 創的圖(預設)
                    #                                             2 = 只回該 group 上傳的圖
                    #                        其中 trigger_chat 預設為 3 個以上的字才回話，可以設為 2~15
                    SystemConfig = SystemConfig[index]
                    reply_content = '[當前模式為]  {}, {}, {} '.format(\
                                    'chat_mode:'+str(SystemConfig[1]), 'retrieve_pic_mode:'+str(SystemConfig[2]), 'trigger_chat:'+str(SystemConfig[3]))
                    LineReplyMsg(event.reply_token, reply_content, content_type='text')

        # elif event.message.text == "--list":
        #     # 撈出除了 pic_name_list 這張圖片以外的所有圖片名稱
        #     select_pre_sql = "SELECT pic_name FROM pic_info WHERE pic_name != 'pic_name_list'"
        #     res = select_from_db(select_pre_sql, select_params_dict={})
        #     # res 格式為:  [('1',), ('ABC',)]
        #     res = [ _[0] for _ in res ]
        #     # 利用 set 將重複的字串給刪去
        #     res = list(set(res))
        #     def render_mpl_table(data, col_width=3.0, row_height=0.625, font_size=12,
        #                         header_color='#40466e', row_colors=['#f1f1f2', 'w'], edge_color='w',
        #                         bbox=[0, 0, 1, 1], header_columns=0,
        #                         ax=None, **kwargs):
        #         print('enter render_mpl_table')
        #         if ax is None:
        #             size = (array(data.shape[::-1]) + array([0, 1])) * array([col_width, row_height])
        #             fig, ax = subplots(figsize=size)
        #             ax.axis('off')
        #         # 取當前 main.py 的檔案位置，因為我上傳的字型檔跟他放一起
        #         dir_path = os.path.dirname(os.path.realpath(__file__))
        #         # STHeitiMedium.ttc 是中文字型檔，有了它 matplotlib 才有辦法印出中文，我擔心 GCP 沒有內建就自己上傳了
        #         font = FontProperties(fname=dir_path+"/STHeitiMedium.ttc", size=14)
        #         mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs)
        #         mpl_table.auto_set_font_size(False)
        #         mpl_table.set_fontsize(font_size)

        #         for k, cell in  iteritems(mpl_table._cells):
        #             cell.set_edgecolor(edge_color)
        #             if k[0] == 0 or k[1] < header_columns:
        #                 # fontproperties=font 這個是表格能不能印出中文的關鍵!
        #                 cell.set_text_props(weight='bold', color='w', fontproperties=font)
        #                 cell.set_facecolor(header_color)
        #             else:
        #                 cell.set_facecolor(row_colors[k[0]%len(row_colors) ])
        #                 # fontproperties=font 這個是表格能不能印出中文的關鍵!
        #                 cell.set_text_props(fontproperties=font)
        #         return ax

        #     def turn_table_into_pic(table_object):
        #         print('enter turn_table_into_pic')
        #         pic = table_object
        #         plt_buf = BytesIO()
        #         pil_buf = BytesIO()
        #         pic.savefig(plt_buf, format='png')
        #         Image.open(plt_buf).save(pil_buf, format="png")
        #         plt_buf.close()
        #         byte_img = pil_buf.getvalue()
        #         pil_buf.close()
        #         return byte_img
            
        #     # 圖片中的 columns 數
        #     columns_cnt = 6
        #     # 取餘數用 None 補滿，讓每個 column 都有內如，pd.DataFrame 才不會變成只有一行
        #     res.extend([None for i in range(len(res) % columns_cnt)])
        #     # 將 list 包成 [ [1,2,3], [1,2,3] ] 這樣的格式再餵給 pd.DataFrame(注意，裡面每個 list 一定要數量一致喔)
        #     res = [ res[i:i + columns_cnt] for i in range(0, len(res), columns_cnt) ]
        #     print('debug res[-1]:', res[-1])
        #     pd_res = DataFrame(res)
        #     table_object = render_mpl_table(pd_res, header_columns=0, col_width=2.0).get_figure()
        #     binary_pic = turn_table_into_pic(table_object)
        #     pic_link, reply_msg = UploadToImgur(Pic_Name='pic_name_list', binary_pic=binary_pic)
        #     update_params_dict = {
        #         'pic_link': pic_link,
        #         'pic_name': 'pic_name_list',
        #         }
        #     # 複寫名字為 'pic_name_list' 的 pic_link
        #     update_pre_sql = "UPDATE pic_info SET pic_link=:pic_link WHERE pic_name = :pic_name"
        #     update_from_db(update_pre_sql, update_params_dict)
        #     LineReplyMsg(event.reply_token, pic_link, content_type='image')

        else:
            select_pre_sql = "SELECT * FROM system WHERE group_id = :group_id"
            SystemConfig = select_from_db(select_pre_sql, select_params_dict={'group_id': group_id})
            print('SystemConfig, group_id', SystemConfig, group_id)
            if not SystemConfig and group_id is not 'NULL':
                print('該群組於System中還沒有資料，建立一筆資料')
                # 如果還沒有 SystemConfig 且有 group_id 那就創一個，只設定 group_id 其他用 default
                insert_pre_sql = "INSERT INTO system (group_id) values (:group_id)"
                insert_from_db(insert_pre_sql, insert_params_dict={'group_id': group_id})
            else:
                print('該群組於System中有資料了，或是是非群組對話')
                group_id_list = [i[0] for i in SystemConfig]
                index = group_id_list.index(group_id)
                print('group_id_list, index', group_id_list, index)
                # SystemConfig[index] 會回傳一個 tuple 類似像 ('Cxxxxxx', 1, 1, 3)
                # 從左至右分別對應: group_id,	chat_mode, retrieve_pic_mode, trigger_chat
                SystemConfig = SystemConfig[index]
                print('SystemConfig[index]', SystemConfig)

                # trigger_chat 判斷
                trigger_chat = SystemConfig[3]
                print('trigger_chat', trigger_chat)
                # chat_mode 判斷
                # 0 = 不回圖
                print('SystemConfig[1]', SystemConfig[1])
                if SystemConfig[1] is 0 :
                    print('chat_mode is 0')
                    return
                # 1 = 隨機回所有 group 創的圖(預設)
                elif SystemConfig[1] is 1 :
                    print('chat_mode is 1')
                    PICLINK = CheckMsgContent(event.message.text, trigger_chat, group_id=None)
                    if PICLINK:
                        print('PICLINK', PICLINK)
                        LineReplyMsg(event.reply_token, PICLINK, content_type='image')
                # 2 = 只回該 group 創的圖
                elif SystemConfig[1] is 2 :
                    # 搜尋時帶上 group_id 判斷是否符合同群組
                    print('chat_mode is 2, group_id:', group_id)
                    PICLINK = CheckMsgContent(event.message.text, trigger_chat, group_id=group_id)
                    if PICLINK:
                        print('PICLINK', PICLINK)
                        LineReplyMsg(event.reply_token, PICLINK, content_type='image')





# SQL 參考：
# 1. https://www.jianshu.com/p/e6bba189fcbd
# 2. https://blog.csdn.net/slvher/article/details/47154363



