# -*- coding: utf-8 -*-
import random
from flask import Flask, request, abort
from linebot import WebhookHandler
from linebot.exceptions import (
    InvalidSignatureError
)
# import tempfile
from imgur_auth import ImgurClient
import re
from base64 import b64encode
from config import *
from models.bot import Bot
from models.chat import Chat


app = Flask(__name__)
# line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
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




# -------------------------------------------------
# -               收到圖片後邏輯                    -
# -------------------------------------------------
# 研究後發現，如果要顧及收到圖片後再上傳這件事情，那將遇到幾個難題
# ~~~~~~先講結論~~~~~ 最後決定，只能確認使用者有先命名完才做上傳動作，確保每一次有確定要上傳才做
# 首先:
# 1. 因為線上會起多個 process 所以將圖片暫存檔記在 memory 有機會是另一個 process 去檢查結果發現沒有圖片
# 2. 而之後有考慮用 pickle 的方式儲存檔案，但 Google Cloud Function 不支援寫檔案的動作所以無法
# 接下來我們有其他作法可以考慮:
# 1. 先存圖片到 DB 再上傳
#    但那將會增加 DB Server 傳輸負擔跟流量成本
# 2. 只要收到圖片一律上傳，如果仍未命名但又有收到圖片，就刪除前一張後再上傳，直到有命名則修改最後一張上傳圖片的名稱為正式名稱
#    但這會增加上傳的成本，依據 Imgur 免費的流量只能上傳 10,000 張圖片每月，就算花 25 鎂也是 60,000 每月，並不能這樣玩
# 最後決定，只能確認使用者有先命名完才做上傳動作，確保每一次有確定要上傳才做
# 與此同時，有考慮每個人是不是要設定 quota 來限制是不是一天只能上傳幾張圖片
# 此部分可能可以在未來自己架設圖片 server 來解決這個問題
# @handler.add(MessageEvent, message=ImageMessage)
# def handle_image(event):
#     user_id = event.source.user_id
#     try:
#         group_id = event.source.group_id
#     except AttributeError as e:
#         group_id = 'NULL'
#         print("send from 1 to 1 chat room, so there's no group id")
#     # 將 user 建檔管理
#     add_userid_if_not_exist(user_id)
#     # 檢查該 user 是否已經被 banned
#     if is_userid_banned(user_id):
#         try:
#             raise Exception(
#                 'This user id' +
#                 str(user_id) +
#                 'got banned, refuse to do anything!')
#         except Exception:
#             logging.warning(
#                 'This user id' +
#                 str(user_id) +
#                 'got banned, refuse to do anything!')
#         return
#     params_dict = {
#         'user_id': user_id,
#         'group_id': group_id,
#     }
#     # 名字設定好但還沒有 pic_link 的且 user_id 符合的就是準備要上傳的
#     select_pre_sql = ("SELECT pic_name FROM pic_info "
#                       "WHERE pic_link IS NULL "
#                       "AND user_id=:user_id "
#                       "AND group_id=:group_id")
#     # 回傳為 list type 裡面包著 tuple 預期一定會拿到 pic_name 所以直接取第一個不怕噴錯
#     pic_name = dbm.select_from_db(select_pre_sql, params_dict)
#     pic_name = pic_name[0][0] if pic_name else None

#     if is_filename_exist(pic_name, group_id):
#         print('name already exist, start to upload')
#         binary_pic = line_bot_api.get_message_content(self.event.message_id).content
#         print('type(binary_pic)', type(binary_pic))
#         pic_link, reply_msg = upload_to_imgur(pic_name, binary_pic=binary_pic)
#         params_dict = {
#             'user_id': user_id,
#             'pic_link': pic_link,
#             'group_id': group_id
#         }
#         # 名字設定好但還沒有 pic_link 的且 user_id 符合的就是剛上傳好的
#         update_pre_sql = ("UPDATE pic_info SET pic_link=:pic_link, group_id=:group_id "
#                           "WHERE user_id=:user_id AND pic_link IS NULL")
#         dbm.iud_from_db(update_pre_sql, params_dict)
#         line_reply_msg(event.reply_token, reply_msg, content_type='text')


# -------------------------------------------------
# -                 收到文字後邏輯                  -
# -------------------------------------------------
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    #TODO 目前沒有儲存 pic_name to DB 的邏輯
    chat = Chat(event)
    if chat.user_banned == True:
        return f'user id: {chat.event.user_id} got banned~!'
    bot = Bot(chat)
    bot.do_skill_or_set_mode()
    bot.send_pic_back()
    del chat, bot

# # -------------------------------------------------
# # -                一般對話處理邏輯                 -
# # -------------------------------------------------
#         else:
#             select_pre_sql = (
#                 "SELECT * FROM system WHERE group_id = :group_id")
#             system_config = dbm.select_from_db(
#                 select_pre_sql, params_dict={
#                     'group_id': group_id})
#             print('system_config, group_id', system_config, group_id)
#             if not system_config and group_id is not 'NULL':
#                 print('該群組於System中還沒有資料，建立一筆資料')
#                 # 如果還沒有 system_config 且有 group_id 那就創一個，只設定 group_id 其他用
#                 # default
#                 insert_pre_sql = (
#                     "INSERT INTO system (group_id) values (:group_id)")
#                 dbm.iud_from_db(
#                     insert_pre_sql, params_dict={
#                         'group_id': group_id})
#             else:
#                 print('該群組於System中有資料了，或是是非群組對話')
#                 group_id_list = [i[0] for i in system_config]
#                 index = group_id_list.index(group_id)
#                 print('group_id_list, index', group_id_list, index)
#                 # system_config[index] 會回傳一個 tuple 類似像 ('Cxxxxxx', 1, 1, 3)
#                 # 從左至右分別對應: group_id,     chat_mode, retrieve_pic_mode,
#                 # trigger_chat
#                 system_config = system_config[index]
#                 print('system_config[index]', system_config)

#                 # trigger_chat 判斷
#                 trigger_chat = system_config[3]
#                 print('trigger_chat', trigger_chat)
#                 # chat_mode 判斷
#                 # 0 = 不回圖
#                 print('system_config[1]', system_config[1])
#                 if system_config[1] is 0:
#                     print('chat_mode is 0')
#                     return
#                 # 1 = 隨機回所有 group 創的圖(預設)
#                 elif system_config[1] is 1:
#                     print('chat_mode is 1')
#                     pic_link = check_msg_content(
#                         event.message.text, trigger_chat, group_id=None)
#                     if pic_link:
#                         print('pic_link', pic_link)
#                         line_reply_msg(
#                             event.reply_token, pic_link, content_type='image')
#                 # 2 = 只回該 group 創的圖
#                 elif system_config[1] is 2:
#                     # 搜尋時帶上 group_id 判斷是否符合同群組
#                     print('chat_mode is 2, group_id:', group_id)
#                     pic_link = check_msg_content(
#                         event.message.text, trigger_chat, group_id=group_id)
#                     if pic_link:
#                         print('pic_link', pic_link)
#                         line_reply_msg(
#                             event.reply_token, pic_link, content_type='image')
