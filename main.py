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
import re
import pickle
import lockfile
import requests
import base64
import json
import base64

app = Flask(__name__)
line_bot_api = LineBotApi(line_channel_access_token)
handler = WebhookHandler(line_channel_secret)
pic_dict_lock = lockfile.LockFile('pic_dict.pickle')
API_URL = 'https://api.imgur.com/'
MASHAPE_URL = 'https://imgur-apiv3.p.mashape.com/'

# 原 imgur_auth 的內容 # 
# class AuthWrapper(object):
#     def __init__(self, access_token, refresh_token, client_id, client_secret):
#         self.current_access_token = access_token

#         if refresh_token is None:
#             raise TypeError('A refresh token must be provided')

#         self.refresh_token = refresh_token
#         self.client_id = client_id
#         self.client_secret = client_secret

#     def get_refresh_token(self):
#         return self.refresh_token

#     def get_current_access_token(self):
#         return self.current_access_token

#     def refresh(self):
#         data = {
#             'refresh_token': self.refresh_token,
#             'client_id': self.client_id,
#             'client_secret': self.client_secret,
#             'grant_type': 'refresh_token'
#         }

#         url = API_URL + 'oauth2/token'

#         response = requests.post(url, data=data)

#         if response.status_code != 200:
#             raise print('Error refreshing access token!', response.status_code)

#         response_data = response.json()
#         self.current_access_token = response_data['access_token']
# class ImgurClient(object):
#     allowed_album_fields = {
#         'ids', 'title', 'description', 'privacy', 'layout', 'cover'
#     }

#     allowed_advanced_search_fields = {
#         'q_all', 'q_any', 'q_exactly', 'q_not', 'q_type', 'q_size_px'
#     }

#     allowed_account_fields = {
#         'bio', 'public_images', 'messaging_enabled', 'album_privacy', 'accepted_gallery_terms', 'username'
#     }

#     allowed_image_fields = {
#         'album', 'name', 'title', 'description'
#     }

#     def __init__(self, client_id, client_secret, access_token=None, refresh_token=None, mashape_key=None):
#         self.client_id = client_id
#         self.client_secret = client_secret
#         self.auth = None
#         self.mashape_key = mashape_key

#         if refresh_token is not None:
#             self.auth = AuthWrapper(access_token, refresh_token, client_id, client_secret)

#         self.credits = self.get_credits()

#     def set_user_auth(self, access_token, refresh_token):
#         self.auth = AuthWrapper(access_token, refresh_token, self.client_id, self.client_secret)

#     def get_client_id(self):
#         return self.client_id

#     def get_credits(self):
#         return self.make_request('GET', 'credits', None, True)

#     def get_auth_url(self, response_type='pin'):
#         return '%soauth2/authorize?client_id=%s&response_type=%s' % (API_URL, self.client_id, response_type)

#     def authorize(self, response, grant_type='pin'):
#         return self.make_request('POST', 'oauth2/token', {
#             'client_id': self.client_id,
#             'client_secret': self.client_secret,
#             'grant_type': grant_type,
#             'code' if grant_type == 'authorization_code' else grant_type: response
#         }, True)

#     def prepare_headers(self, force_anon=False):
#         headers = {}
#         if force_anon or self.auth is None:
#             if self.client_id is None:
#                 raise ImgurClientError('Client credentials not found!')
#             else:
#                 headers['Authorization'] = 'Client-ID %s' % self.get_client_id()
#         else:
#             headers['Authorization'] = 'Bearer %s' % self.auth.get_current_access_token()

#         if self.mashape_key is not None:
#             headers['X-Mashape-Key'] = self.mashape_key

#         return headers


#     def make_request(self, method, route, data=None, force_anon=False):
#         method = method.lower()
#         method_to_call = getattr(requests, method)

#         header = self.prepare_headers(force_anon)
#         url = (MASHAPE_URL if self.mashape_key is not None else API_URL) + ('3/%s' % route if 'oauth2' not in route else route)

#         if method in ('delete', 'get'):
#             response = method_to_call(url, headers=header, params=data, data=data)
#         else:
#             response = method_to_call(url, headers=header, data=data)

#         if response.status_code == 403 and self.auth is not None:
#             self.auth.refresh()
#             header = self.prepare_headers()
#             if method in ('delete', 'get'):
#                 response = method_to_call(url, headers=header, params=data, data=data)
#             else:
#                 response = method_to_call(url, headers=header, data=data)

#         self.credits = {
#             'UserLimit': response.headers.get('X-RateLimit-UserLimit'),
#             'UserRemaining': response.headers.get('X-RateLimit-UserRemaining'),
#             'UserReset': response.headers.get('X-RateLimit-UserReset'),
#             'ClientLimit': response.headers.get('X-RateLimit-ClientLimit'),
#             'ClientRemaining': response.headers.get('X-RateLimit-ClientRemaining')
#         }

#         # Rate-limit check
#         if response.status_code == 429:
#             raise print('429 error')

#         try:
#             response_data = response.json()
#         except:
#             raise print('JSON decoding of response failed.')

#         if 'data' in response_data and isinstance(response_data['data'], dict) and 'error' in response_data['data']:
#             raise print(response_data['data']['error'], response.status_code)

#         return response_data['data'] if 'data' in response_data else response_data

#     def validate_user_context(self, username):
#         if username == 'me' and self.auth is None:
#             raise print('\'me\' can only be used in the authenticated context.')

#     def logged_in(self):
#         if self.auth is None:
#             raise print('Must be logged in to complete request.')

#     # Account-related endpoints
#     def get_account(self, username):
#         self.validate_user_context(username)
#         account_data = self.make_request('GET', 'account/%s' % username)

#         return Account(
#             account_data['id'],
#             account_data['url'],
#             account_data['bio'],
#             account_data['reputation'],
#             account_data['created'],
#             account_data['pro_expiration'],
#         )
# ###################################################
# def WritePickleFile(str_file_path, content):
#     with open (str_file_path, 'wb') as file:
#         pickle.dump(content, file)

# def LoadPickleFile(str_file_path):
#     with open (str_file_path, 'rb') as file:
#         global PicNameDict
#         PicNameDict = pickle.load(file)

# def AddToPicDict(pic_name, pic_id):
#     # check file is locked
#     LoadPickleFile('pic_dict.pickle')
#     if pic_dict_lock.is_locked() is True and PicNameDict.get('isLock') is True : return False
#     # double confirm 'isLock' value is not True
#     LoadPickleFile('pic_dict.pickle')
#     if PicNameDict.get('isLock') is True : return False
#     # lock the file
#     pic_dict_lock.acquire()
#     # Set isLock to True, let the other process knows that I'm editing this file
#     PicNameDict['isLock'] = True
#     WritePickleFile('pic_dict.pickle', PicNameDict) 
#     PicNameDict[pic_name] = pic_id ; PicNameDict['isLock'] = False
#     WritePickleFile('pic_dict.pickle', PicNameDict)
#     # unlock the file
#     pic_dict_lock.break_lock()
#     if pic_dict_lock.is_locked() is not True and PicNameDict.get('isLock') is not True : return True

# def DeleteFromPicDict(pic_name):
#     # check file is locked
#     LoadPickleFile('pic_dict.pickle')
#     if pic_dict_lock.is_locked() is True and PicNameDict.get('isLock') is True : return False
#     # double confirm 'isLock' value is not True
#     LoadPickleFile('pic_dict.pickle')
#     if PicNameDict.get('isLock') is True : return False
#     # lock the file
#     pic_dict_lock.acquire()
#     # Set isLock to True, let the other process knows that I'm editing this file
#     PicNameDict['isLock'] = True
#     WritePickleFile('pic_dict.pickle', PicNameDict)
#     PicNameDict.pop(pic_name) ; PicNameDict['isLock'] = False
#     WritePickleFile('pic_dict.pickle', PicNameDict)
#     # unlock the file
#     pic_dict_lock.break_lock()
#     if pic_dict_lock.is_locked() is not True and PicNameDict.get('isLock') is not True : return True

@app.route("/callback", methods=['POST'])
def callback(event):
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    
    # get request body as text
    body = request.get_data(as_text=True)
    # app.logger.info("Request body: " + body)
    
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# def isFileExist(event, user_id):
#     '''
#     input = event.source.user_id
#     output = Ture or False 
#     '''
#     print('enter FileExist')
#     Files_In_tmp = os.listdir(os.getcwd()+'/static/tmp')
#     for file_name in Files_In_tmp:
#         File_Exist = True if re.search(str(user_id), file_name) else False
#         if File_Exist:
#             print('File_Exist:', File_Exist) #debug
#             return True
#     print('File_Exist:', File_Exist) #debug    
#     return False

# def isFileNameExist(event, user_id):
#     print('enter FileNameExist')
#     LoadPickleFile('pic_dict.pickle')
#     print('PicNameDict:'+str(PicNameDict)) #debug
#     for file in list(PicNameDict):
#         File_Name_Exist = True if re.search(str(user_id), file) else False
#         if File_Name_Exist:
#             print('File_Name_Exist:', File_Name_Exist) #debug
#             return True
#     print('File_Name_Exist:', File_Name_Exist) #debug
#     return False

# def GetPic(event, user_id, group_id, message_id):
#     print('enter GetPic')
#     message_content = line_bot_api.get_message_content(message_id)
#     File_Name_Ext = "{0}{1}{2}".format('WHOS_PICNAME_', str(user_id), '.jpg')
#     File_Path = os.path.join(os.path.dirname(__file__), 'static', 'tmp', File_Name_Ext)
#     with open(File_Path, 'wb+') as tf:
#         for chunk in message_content.iter_content():
#             tf.write(chunk)
#         Tempfile_Path = tf.name
#     to = group_id if group_id else user_id
#     line_bot_api.push_message(
#         to,
#         TextSendMessage(text='File_Path:{}, File_Name_Ext:{}'.format(Tempfile_Path, File_Name_Ext))
#     ) #debug
#     line_bot_api.push_message(
#         to,
#         TextSendMessage(text='已儲存圖片暫存檔')
#     )
#     return True if isFileNameExist(event, user_id) else False

# def UploadToImgur(event, user_id, group_id):
#     print('enter UploadToImgur')
#     Pic_Name = PicNameDict.get('WHOS_PICNAME_' + str(user_id))
#     try:
#         print('UploadToImgur Pic_Name: ' + Pic_Name) #debug
#         path = os.path.join('static', 'tmp', 'WHOS_PICNAME_' + str(user_id) + '.jpg')
#         print('path:'+path) #debug
#         ########### 嘗試改用 python requests + API 的 headers 與 auth ###########
#         with open (path, 'rb') as file:
#             byte_file = file.read()
#             payload = base64.b64encode(byte_file)
#         data = {
#             'image': payload,
#             'album': Album_ID,
#             'name': Pic_Name,
#             'title': Pic_Name,
#             'description': 'Upload From MemePicLineBot'
#         }
#         # 這邊要考慮在 description 中加入 sha256 加密過的使用者 line user id 來達到嚇阻避免使用者濫用，濫用情況類似像是 PO 違法照片等等
#         # 也要想方法公告表示不要將個人資料與非法照片上傳（類似裸照或是未成年照片等等，我不想被ＦＢＩ抓．．．）否則將依法究辦之類的
#         InstanceClient = ImgurClient(client_id, client_secret, access_token, refresh_token)
#         headers = InstanceClient.prepare_headers()
#         response = requests.post('https://api.imgur.com/3/image', headers=headers, data=data)
#         pic_link = json.loads(response.text)['data']['link']
#         ########################################################################
#         print(os.listdir(os.getcwd()+'/static/tmp')) #debug
#         print('104 remove path'+path) #debug
#         to = group_id if group_id else user_id
#         line_bot_api.push_message(
#             to,
#             TextSendMessage(text='上傳至Imgur成功, pic link: '+str(pic_link))
#             )
#         line_bot_api.push_message(
#                     to,
#                     ImageSendMessage(preview_image_url=pic_link,
#                                     original_content_url=pic_link)
#                 )
#     except Exception as e:
#         print(e)
#         to = group_id if group_id else user_id
#         line_bot_api.push_message(
#             to,
#             TextSendMessage(text='上傳至Imgur失敗'))

# def RemovePic(event, user_id, group_id):
#     '''
#     刪除檔案及從 PicNameDict 中去除
#     '''
#     # 刪除圖片檔
#     path = os.path.join('static', 'tmp', 'WHOS_PICNAME_' + str(user_id) + '.jpg')
#     os.remove(path)
#     print(os.listdir(os.getcwd()+'/static/tmp')) #debug
#     print('122 group_id: ')  #debug
#     print('group_id:'+str(group_id)) #debug
#     print('type of group_id:' + str(type(group_id))) #debug
#     to = group_id if group_id else user_id
#     line_bot_api.push_message(
#         to,
#         TextSendMessage(text='刪除圖片暫存檔'))

# def SavePicNameIntoDict(event, user_id, group_id, Line_Msg_Text):
#     print('enter SavePicNameIntoDict')
#     '''
#     以 WHOS_PICNAME_user_id 的格式儲存圖片名稱
#     若已經存在則複寫
#     '''
#     AddToPicDict('WHOS_PICNAME_' + str(user_id), Line_Msg_Text[1:-1])
#     to = group_id if group_id else user_id
#     line_bot_api.push_message(
#         to,
#         TextSendMessage(text='144 id, PicNameDict:{}{}, pid:{}'.format(id(PicNameDict), PicNameDict, os.getpid()))
#         )
#     line_bot_api.push_message(
#         to,
#         TextSendMessage(text='圖片名字已設定完成: ' + Line_Msg_Text[1:-1])
#         )
#     return True

# # #################################################
# #                收到圖片後邏輯
# # #################################################
# @handler.add(MessageEvent, message=ImageMessage)
# def handle_image(event):
#     user_id = event.source.user_id
#     message_id = event.message.id
#     try:
#         group_id = event.source.group_id
#     except AttributeError as e:
#         group_id = None
#         print("send from 1 to 1 chat room, so there's no group id")

#     if isFileExist(event, user_id):
#         ''' 如果圖片暫存檔已經存在 '''
#         print('File Exist('+str(user_id)+'), remove pic file') #debug
#         RemovePic(event, user_id, group_id)
#         print('RemovePic done')
#         GetPic(event, user_id, group_id, message_id)
#         print('GetPic done')
#         to = group_id if group_id else user_id
#         line_bot_api.push_message(
#             to,
#             TextSendMessage(text='232 if isFileExist('+str(user_id)+')')
#             )
#         if isFileNameExist(event, user_id):
#             ''' 檔案名稱已取好了 '''
#             print('name already exist, start to upload')
#             UploadToImgur(event, user_id, group_id)
#             RemovePic(event, user_id, group_id)
#             DeleteFromPicDict('WHOS_PICNAME_' + str(user_id))
#         else:
#             ''' 檔案名稱還沒取好 '''
#             line_bot_api.push_message(
#                 to,
#                 TextSendMessage(text='檔案已存成暫存檔，請設定圖片名稱，範例: #圖片名稱#')
#                 )
#     else:
#         ''' 如果圖片還沒上傳過 '''
#         print('239 File Not Exist('+str(user_id)+'), get pic directly') #debug
#         to = group_id if group_id else user_id
#         line_bot_api.push_message(
#             to,
#             TextSendMessage(text='243 else isFileExist('+str(user_id)+')')
#             )
#         GetPic(event, user_id, group_id, message_id)
#         if isFileNameExist(event, user_id):
#             ''' 檔案名稱已取好了 '''
#             UploadToImgur(event, user_id, group_id)
#             line_bot_api.push_message(
#                 to,
#                 TextSendMessage(text='236 id, PicNameDict:{}{}'.format(id(PicNameDict),PicNameDict))
#                 )
#             RemovePic(event, user_id, group_id)
#             # 刪除 WHOS_PICNAME_user_id 變成未命名狀態
#             DeleteFromPicDict('WHOS_PICNAME_' + str(user_id))
#             print('257 make sure pop'+str(PicNameDict)) # debug
#         else:
#             ''' 檔案名稱還沒取好 '''
#             line_bot_api.push_message(
#                 to,
#                 TextSendMessage(text='檔案已存成暫存檔，請設定圖片名稱，範例: #圖片名稱#')
#                 )

# # #################################################
# #                   收到文字後邏輯
# # #################################################
# @handler.add(MessageEvent, message=TextMessage)    
# def handle_text(event):
#     user_id = event.source.user_id
#     message_id = event.message.id
#     try:
#         group_id = event.source.group_id
#     except AttributeError as e:
#         group_id = None
#         print("send from 1 to 1 chat room, so there's no group id")
#     Line_Msg_Text = event.message.text

#     if isinstance(event.message, TextMessage):
#         if event.message.text[0] == "#" and event.message.text[-1] == "#":
#             print('enter event.message.text[0] == "#" and event.message.text[-1] == "#"') #debug
#             # SavePicNameIntoDict(event, user_id, group_id, Line_Msg_Text)
#             # 因為會覆寫，所以直接在 Add 一次不用刪除
#             AddToPicDict('WHOS_PICNAME_' + str(user_id), Line_Msg_Text[1:-1])
#             if isFileExist(event, user_id):
#                 UploadToImgur(event, user_id, group_id)
#                 RemovePic(event, user_id, group_id)
#             else:
#                 to = group_id if group_id else user_id
#                 line_bot_api.push_message(
#                     to,
#                     TextSendMessage(text='圖片名稱已設定完畢，請上傳圖片')
#                 )
#         elif event.message.text == "--help":
#             print('event.message.text == "--help"') #debug
#             to = group_id if group_id else user_id
#             line_bot_api.push_message(
#                     to,
#                     TextSendMessage(text='請使用 "#"+"圖片名稱"+"#" 來設定圖片名稱，範例: #圖片名稱#')
#                 )
#             line_bot_api.push_message(
#                     to,
#                     ImageSendMessage(preview_image_url='https://steemitimages.com/DQmPfGvYUqg9TUsaK8EUegqL2gVGR8FSS67FtYRs86UfUP1/help-and-support.png',
#                                     original_content_url='https://steemitimages.com/DQmPfGvYUqg9TUsaK8EUegqL2gVGR8FSS67FtYRs86UfUP1/help-and-support.png')
#                 )