# -*- coding: utf-8 -*-
import random
from flask import Flask, request, abort
from imgurpython import ImgurClient
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
from imgur_auth import ImgurClient

app = Flask(__name__)
line_bot_api = LineBotApi(line_channel_access_token)
handler = WebhookHandler(line_channel_secret)
pic_dict_lock = lockfile.LockFile('pic_dict.pickle')

def WritePickleFile(str_file_path, content):
    with open (str_file_path, 'wb') as file:
        pickle.dump(content, file)

def LoadPickleFile(str_file_path):
    with open (str_file_path, 'rb') as file:
        global PicNameDict
        PicNameDict = pickle.load(file)

def AddToPicDict(pic_name, pic_id):
    # check file is locked
    LoadPickleFile('pic_dict.pickle')
    if pic_dict_lock.is_locked() is True and PicNameDict['isLock'] is True : return False
    # double confirm 'isLock' value is not True
    LoadPickleFile('pic_dict.pickle')
    if PicNameDict['isLock'] is True : return False
    # lock the file
    pic_dict_lock.acquire()
    # Set isLock to True, let the other process knows that I'm editing this file
    PicNameDict['isLock'] = True
    WritePickleFile('pic_dict.pickle', PicNameDict) 
    PicNameDict[pic_name] = pic_id ; PicNameDict['isLock'] = False
    WritePickleFile('pic_dict.pickle', PicNameDict)
    # unlock the file
    pic_dict_lock.break_lock()
    if pic_dict_lock.is_locked() is not True and PicNameDict['isLock'] is not True : return True

def DeleteFromPicDict(pic_name):
    # check file is locked
    LoadPickleFile('pic_dict.pickle')
    if pic_dict_lock.is_locked() is True and PicNameDict['isLock'] is True : return False
    # double confirm 'isLock' value is not True
    LoadPickleFile('pic_dict.pickle')
    if PicNameDict['isLock'] is True : return False
    # lock the file
    pic_dict_lock.acquire()
    # Set isLock to True, let the other process knows that I'm editing this file
    PicNameDict['isLock'] = True
    WritePickleFile('pic_dict.pickle', PicNameDict)
    PicNameDict.pop(pic_name) ; PicNameDict['isLock'] = False
    WritePickleFile('pic_dict.pickle', PicNameDict)
    # unlock the file
    pic_dict_lock.break_lock()
    if pic_dict_lock.is_locked() is not True and PicNameDict['isLock'] is not True : return True

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

def isFileExist(event, user_id):
    '''
    input = event.source.user_id
    output = Ture or False 
    '''
    print('enter FileExist')
    Files_In_tmp = os.listdir(os.getcwd()+'/static/tmp')
    for file_name in Files_In_tmp:
        File_Exist = True if re.search(str(user_id), file_name) else False
        if File_Exist:
            print('File_Exist:', File_Exist) #debug
            return True
    print('File_Exist:', File_Exist) #debug    
    return False

def isFileNameExist(event, user_id):
    print('enter FileNameExist')
    LoadPickleFile('pic_dict.pickle')
    print('PicNameDict:'+str(PicNameDict)) #debug
    for file in list(PicNameDict):
        File_Name_Exist = True if re.search(str(user_id), file) else False
        if File_Name_Exist:
            print('File_Name_Exist:', File_Name_Exist) #debug
            return True
    print('File_Name_Exist:', File_Name_Exist) #debug
    return False

def GetPic(event, user_id, group_id, message_id):
    print('enter GetPic')
    message_content = line_bot_api.get_message_content(message_id)
    File_Name_Ext = "{0}{1}{2}".format('WHOS_PICNAME_', str(user_id), '.jpg')
    File_Path = os.path.join(os.path.dirname(__file__), 'static', 'tmp', File_Name_Ext)
    with open(File_Path, 'wb+') as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        Tempfile_Path = tf.name
    to = group_id if group_id else user_id
    line_bot_api.push_message(
        to,
        TextSendMessage(text='File_Path:{}, File_Name_Ext:{}'.format(Tempfile_Path, File_Name_Ext))
    ) #debug
    line_bot_api.push_message(
        to,
        TextSendMessage(text='已儲存圖片暫存檔')
    )
    return True if isFileNameExist(event, user_id) else False

def UploadToImgur(event, user_id, group_id):
    print('enter UploadToImgur')
    Pic_Name = PicNameDict['WHOS_PICNAME_' + str(user_id)]
    try:
        print('UploadToImgur Pic_Name: ' + Pic_Name) #debug
        path = os.path.join('static', 'tmp', 'WHOS_PICNAME_' + str(user_id) + '.jpg')
        print('path:'+path) #debug
        ########### 嘗試改用 python requests + API 的 headers 與 auth ###########
        with open (path, 'rb') as file:
            byte_file = file.read()
            payload = base64.b64encode(byte_file)
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
        client.upload_from_path(path, config=config, anon=False)
        print(os.listdir(os.getcwd()+'/static/tmp')) #debug
        print('104 remove path'+path) #debug
        to = group_id if group_id else user_id
        line_bot_api.push_message(
            to,
            TextSendMessage(text='上傳至Imgur成功'))
    except Exception as e:
        print(e)
        to = group_id if group_id else user_id
        line_bot_api.push_message(
            to,
            TextSendMessage(text='上傳至Imgur失敗'))

def RemovePic(event, user_id, group_id):
    '''
    刪除檔案及從 PicNameDict 中去除
    '''
    # 刪除圖片檔
    path = os.path.join('static', 'tmp', 'WHOS_PICNAME_' + str(user_id) + '.jpg')
    os.remove(path)
    print(os.listdir(os.getcwd()+'/static/tmp')) #debug
    print('122 group_id: ')  #debug
    print(group_id) #debug
    print(type(group_id)) #debug
    # 刪除 WHOS_PICNAME_user_id 變成未命名狀態
    DeleteFromPicDict('WHOS_PICNAME_' + str(user_id))
    print('128 make sure pop'+str(PicNameDict)) # debug
    to = group_id if group_id else user_id
    line_bot_api.push_message(
        to,
        TextSendMessage(text='刪除圖片'))

def SavePicNameIntoDict(event, user_id, group_id, Line_Msg_Text):
    print('enter SavePicNameIntoDict')
    '''
    以 WHOS_PICNAME_user_id 的格式儲存圖片名稱
    若已經存在則複寫
    '''
    # PicNameDict['WHOS_PICNAME_' + str(user_id)] = Line_Msg_Text[1:-1]
    AddToPicDict('WHOS_PICNAME_' + str(user_id), Line_Msg_Text[1:-1])
    # PicNameDict.update({ 'WHOS_PICNAME_' + str(user_id) : Line_Msg_Text[1:-1] })
    to = group_id if group_id else user_id
    line_bot_api.push_message(
        to,
        TextSendMessage(text='144 id, PicNameDict:{}{}, pid:{}'.format(id(PicNameDict), PicNameDict, os.getpid()))
        )
    line_bot_api.push_message(
        to,
        TextSendMessage(text='圖片名字已設定完成: ' + Line_Msg_Text[1:-1])
        )
    return True

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

    if isFileExist(event, user_id):
        print('if isFileExist('+str(user_id)+')') #debug
        RemovePic(event, user_id, group_id)
        print('RemovePic done')
        GetPic(event, user_id, group_id, message_id)
        print('GetPic done')
        to = group_id if group_id else user_id
        line_bot_api.push_message(
            to,
            TextSendMessage(text='167 if isFileExist('+str(user_id)+')')
            )
        if isFileNameExist(event, user_id):
            print('name already exist, start to upload')
            UploadToImgur(event, user_id, group_id)
            RemovePic(event, user_id, group_id)
    else:
        print('226 else isFileNameExist('+str(user_id)+')') #debug
        to = group_id if group_id else user_id
        line_bot_api.push_message(
            to,
            TextSendMessage(text='226 else isFileNameExist('+str(user_id)+')')
            )
        GetPic(event, user_id, group_id, message_id)
        if isFileNameExist(event, user_id):
            UploadToImgur(event, user_id, group_id)
            line_bot_api.push_message(
                to,
                TextSendMessage(text='236 id, PicNameDict:{}{}'.format(id(PicNameDict),PicNameDict))
                )
            RemovePic(event, user_id, group_id)
        else:
            line_bot_api.push_message(
                to,
                TextSendMessage(text='檔案已上傳，請設定圖片名稱，範例: #圖片名稱#')
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

    if isinstance(event.message, TextMessage):
        if event.message.text[0] == "#" and event.message.text[-1] == "#":
            print('enter event.message.text[0] == "#" and event.message.text[-1] == "#"') #debug
            SavePicNameIntoDict(event, user_id, group_id, Line_Msg_Text)
            if isFileExist(event, user_id):
                UploadToImgur(event, user_id, group_id)
                RemovePic(event, user_id, group_id)
        elif event.message.text == "--help":
            print('event.message.text == "--help"') #debug
            to = group_id if group_id else user_id
            line_bot_api.push_message(
                    to,
                    TextSendMessage(text='請使用 "#"+"圖片名稱"+"#" 來設定圖片名稱，範例: #圖片名稱#')
                )


if __name__ == "__main__":
    app.run()