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
from config import client_id, client_secret, album_id, access_token, refresh_token, line_channel_access_token, \
    line_channel_secret
import re

imgur_album_id = 'UxgXZbe'
app = Flask(__name__)
line_bot_api = LineBotApi(line_channel_access_token)
handler = WebhookHandler(line_channel_secret)
PicNameDict = {}

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
        File_Exist = True if re.match(str(user_id), file_name) else False
        if File_Exist:
            print('File_Exist:', File_Exist) #debug
            return True
    return False

def isFileNameExist(event, user_id, group_id):
    print('enter FileNameExist')
    print('55 id, PicNameDict:',id(PicNameDict),PicNameDict) #debug
    line_bot_api.push_message(
        group_id,
        TextSendMessage(text='58 id, PicNameDict:{}{}'.format(id(PicNameDict),PicNameDict))
        ) #debug
    for file in list(PicNameDict):
        File_Name_Exist = True if re.search(str(user_id), file) else False
        if File_Name_Exist:
            print('File_Name_Exist:', File_Name_Exist) #debug
            return True
    return False

def GetPic(event, user_id, group_id, message_id):
    print('enter CreateFile')
    message_content = line_bot_api.get_message_content(message_id)
    print('70 id, PicNameDict:',id(PicNameDict),PicNameDict) #debug
    File_Name_Ext = "{0}{1}{2}".format('WHOS_PICNAME_', str(user_id), '.jpg')
    File_Path = os.path.join(os.path.dirname(__file__), 'static', 'tmp', File_Name_Ext)
    with open(File_Path, 'wb+') as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        Tempfile_Path = tf.name
    line_bot_api.push_message(
        group_id,
        TextSendMessage(text='File_Path:{}, File_Name_Ext:{}'.format(File_Path, File_Name_Ext))
    ) #debug
    line_bot_api.push_message(
        group_id,
        TextSendMessage(text='已儲存圖片暫存檔')
    )
    return True if isFileNameExist(event, user_id, group_id) else False

def UploadToImgur(event, user_id, group_id):
    print('enter UploadToImgur')
    print('89 id, PicNameDict:',id(PicNameDict),PicNameDict) #debug
    Pic_Name = PicNameDict['WHOS_PICNAME_' + str(user_id)]
    try:
        print('UploadToImgur Pic_Name: ' + Pic_Name)
        client = ImgurClient(client_id, client_secret, access_token, refresh_token)
        config = {
            'album': imgur_album_id,
            'name': Pic_Name,
            'title': Pic_Name,
            'description': ' '
        }
        path = os.path.join('static', 'tmp', 'WHOS_PICNAME_' + str(user_id) + '.jpg')
        print('path:'+path) #debug
        client.upload_from_path(path, config=config, anon=False)
        print(os.listdir(os.getcwd()+'/static/tmp')) #debug
        print('104 remove path'+path) #debug
        line_bot_api.push_message(
            group_id,
            TextSendMessage(text='上傳成功'))
    except Exception as e:
        print(e)
        line_bot_api.push_message(
            group_id,
            TextSendMessage(text='上傳失敗'))

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
    print('126 id, PicNameDict:',id(PicNameDict),PicNameDict) #debug
    PicNameDict.pop('WHOS_PICNAME_' + str(user_id))
    print('128 make sure pop'+str(PicNameDict)) # debug
    line_bot_api.push_message(
        group_id,
        TextSendMessage(text='刪除圖片'))

def SavePicNameIntoDict(event, user_id, group_id, Line_Msg_Text):
    print('enter SavePicNameIntoDict')
    '''
    以 WHOS_PICNAME_user_id 的格式儲存圖片名稱
    若已經存在則複寫
    '''
    # PicNameDict['WHOS_PICNAME_' + str(user_id)] = Line_Msg_Text[1:-1]
    PicNameDict.update({ 'WHOS_PICNAME_' + str(user_id) : Line_Msg_Text[1:-1] })
    print('141 id, PicNameDict:',id(PicNameDict),PicNameDict) #debug
    line_bot_api.push_message(
        group_id,
        TextSendMessage(text='144 id, PicNameDict:{}{}'.format(id(PicNameDict),PicNameDict))
        )
    line_bot_api.push_message(
        group_id,
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
    group_id = event.source.group_id

    if isFileExist(event, user_id):
        print('if isFileExist(user_id)') #debug
        RemovePic(event, user_id, group_id)
        GetPic(event, user_id, group_id, message_id)
        line_bot_api.push_message(
            group_id,
            TextSendMessage(text='167 if isFileExist(user_id)')
            )
        if isFileNameExist(event, user_id, group_id):
            UploadToImgur(event, user_id, group_id)
            RemovePic(event, user_id, group_id)
    elif isFileNameExist(event, user_id, group_id):
        print('if isFileNameExist(user_id)') #debug
        line_bot_api.push_message(
            group_id,
            TextSendMessage(text='176 elif isFileNameExist(user_id)')
            )
        GetPic(event, user_id, group_id, message_id)
        UploadToImgur(event, user_id, group_id) 
        print('180 make sure pop'+str(PicNameDict)) # debug
        line_bot_api.push_message(
            group_id,
            TextSendMessage(text='183 id, PicNameDict:{}{}'.format(id(PicNameDict),PicNameDict))
            )
        RemovePic(event, user_id, group_id)

# #################################################
#                收到文字後邏輯
# #################################################
@handler.add(MessageEvent, message=TextMessage)    
def handle_text(event):
    user_id = event.source.user_id
    message_id = event.message.id
    group_id = event.source.group_id
    Line_Msg_Text = event.message.text

    if isinstance(event.message, TextMessage):
        if event.message.text[0] == "#" and event.message.text[-1] == "#":
            print('enter event.message.text[0] == "#" and event.message.text[-1] == "#"') #debug
            SavePicNameIntoDict(event, user_id, group_id, Line_Msg_Text)
            if isFileExist(event, user_id):
                UploadToImgur(event, user_id, group_id)
                RemovePic(event, user_id, group_id)
                print('204 id, PicNameDict:',id(PicNameDict),PicNameDict) #debug
        elif event.message.text == "--help":
            print('event.message.text == "--help"') #debug
            line_bot_api.push_message(
                    group_id,
                    TextSendMessage(text='請使用 "#"+"圖片名稱"+"#" 來設定圖片名稱，範例: #我是檔名#')
                )


if __name__ == "__main__":
    app.run()
