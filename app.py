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
# line_channel_access_token = 'FxI3Qlfn3Mwyne/OujcIsYfOQCcIOZTUIYbDF2d41/GZAlQv2p5FGkp/ategG6xe0ErAsJCQOeHxdSM1xJ7uCejar1IGM5tDCzSFp40QmWs0BEjVec2nkacPIrL8Hh8XVvBxUgEUsGG6U+nvyGRClgdB04t89/1O/w1cDnyilFU='
# line_channel_secret = '7c2930cb70180aae136f76504fba88bd'
# client_id = 'ef420e58e8af248'
# client_secret = '461a057a65611590954d7692f78964920b484929'
# album_id = 'UxgXZbe'
# access_token = 'YOUR_IMGUR_ACCESS_TOKEN'
# refresh_token = 'YOUR_IMGUR_ACCESS_TOKEN'

# line_bot_api = LineBotApi()
# handler = WebhookHandler('')
# imgur_client_id = ef420e58e8af248 
# imgur_client_secret = 461a057a65611590954d7692f78964920b484929	
imgur_album_id = 'UxgXZbe'
app = Flask(__name__)
line_bot_api = LineBotApi(line_channel_access_token)
handler = WebhookHandler(line_channel_secret)


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

@handler.add(MessageEvent, message=(ImageMessage, TextMessage))
def handle_message(event):
    print('enter handle_message')
    PicNameDict = {}
    print('default PicNameDict id: ', id(PicNameDict))
    def SavePicNameIntoDict(Line_Msg_Text):
        print('enter SavePicNameIntoDict')
        '''
        以 WHOS_PICNAME_user_id 的格式儲存圖片名稱
        '''
        global PicNameDict
        PicNameDict['WHOS_PICNAME_' + str(event.source.user_id)] = Line_Msg_Text[1:-1]
        print('59 id, PicNameDict:',id(PicNameDict),PicNameDict) #debug
        line_bot_api.reply_message(
            event.reply_token, [
            TextSendMessage(text='圖片名字已設定完成: ' + Line_Msg_Text[1:-1])
            ])
        return True
    
    def FileExist():
        print('enter FileExist')
        Files_In_tmp = os.listdir(os.getcwd()+'/static/tmp')
        for file_name in Files_In_tmp:
            File_Exist = True if re.match(str(event.source.user_id), file_name) else False
            if File_Exist:
                print('File_Exist:', File_Exist) #debug
                return True
        return False
    
    def FileNameExist():
        print('enter FileNameExist')
        global PicNameDict
        print('80 id, PicNameDict:',id(PicNameDict),PicNameDict) #debug
        for file in list(PicNameDict):
            File_Name_Exist = True if re.search(str(event.source.user_id), file) else False
            if File_Name_Exist:
                print('File_Name_Exist:', File_Name_Exist) #debug
                return True
        return False
    
    def CreateFile():
        print('enter CreateFile')
        global PicNameDict
        message_content = line_bot_api.get_message_content(event.message.id)
        print('92 id, PicNameDict:',id(PicNameDict),PicNameDict) #debug
        File_Name_Ext = "{0}{1}{2}".format('WHOS_PICNAME_', str(event.source.user_id), '.jpg')
        File_Path = os.path.join(os.path.dirname(__file__), 'static', 'tmp', File_Name_Ext)
        with open(File_Path, 'wb+') as tf:
            for chunk in message_content.iter_content():
                tf.write(chunk)
            Tempfile_Path = tf.name
        return True
            
    def GetPic():
        print('enter GetPic')
        global PicNameDict
        message_content = line_bot_api.get_message_content(event.message.id)
        # 確認是否為設定名字的人上傳的圖片
        # if User_ID_Who_Upload_Pic != User_ID_Who_Set_Name:
            # print('not the same people upload pic, drop it! return False!')
            # return False
        print('109 id, PicNameDict:',id(PicNameDict),PicNameDict) #debug
        CreateFile()
        print("111 os.listdir(os.getcwd()+'/static/tmp')")
        print(os.listdir(os.getcwd()+'/static/tmp'))
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(text='已儲存圖片暫存檔')
            ])
        return True

    def UploadToImgur():
        print('enter UploadToImgur')
        global PicNameDict
        print('122 id, PicNameDict:',id(PicNameDict),PicNameDict) #debug
        Pic_Name = PicNameDict['WHOS_PICNAME_' + str(event.source.user_id)]
        try:
            print('UploadToImgur Pic_Name: ' + Pic_Name)
            client = ImgurClient(client_id, client_secret, access_token, refresh_token)
            config = {
                'album': imgur_album_id,
                'name': Pic_Name,
                'title': Pic_Name,
                'description': ' '
            }
            path = os.path.join('static', 'tmp', 'WHOS_PICNAME_' + str(event.source.user_id) + '.jpg')
            print('path:'+path) #debug
            client.upload_from_path(path, config=config, anon=False)
            print(os.listdir(os.getcwd()+'/static/tmp')) #debug
            print('132 remove path'+path) #debug
            # 刪除圖片檔
            os.remove(path)
            print(os.listdir(os.getcwd()+'/static/tmp')) #debug
            print(dir(event.source)) #debug
            print('145 event.source.group_id: ')  #debug
            print(event.source.group_id) #debug
            print(type(event.source.group_id)) #debug
            line_bot_api.push_message(
                event.source.group_id,
                TextSendMessage(text='上傳成功'))
            # 刪除 WHOS_PICNAME_user_id 變成未命名狀態
            print('149 id, PicNameDict:',id(PicNameDict),PicNameDict) #debug
            PicNameDict.pop('WHOS_PICNAME_' + str(event.source.user_id))
            print('150 make sure pop'+str(PicNameDict)) # debug
        except Exception as e:
            print(e)
            line_bot_api.push_message(
                event.source.group_id,
                TextSendMessage(text='上傳失敗'))
# #################################################
#                收到訊息後的判斷
# #################################################
    
    if isinstance(event.message, TextMessage):
        if event.message.text[0] == "#" and event.message.text[-1] == "#":
            print('enter event.message.text[0] == "#" and event.message.text[-1] == "#"') #debug
            SavePicNameIntoDict(event.message.text)
            if FileExist():
                UploadToImgur() 
            print('167 id, PicNameDict:',id(PicNameDict),PicNameDict) #debug
        elif event.message.text == "--help":
            print('event.message.text == "--help"') #debug
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage(text='請使用 "#"+"圖片名稱"+"#" 來設定圖片名稱，範例: #我是檔名#')
                ])
    elif isinstance(event.message, ImageMessage):
        print('elif isinstance(event.message, ImageMessage)') #debug
        GetPic()
        if FileNameExist():
            print('if FileNameExist()') #debug
            UploadToImgur() 
            print('177 make sure pop'+str(PicNameDict)) # debug
            
    # elif isinstance(event.message, TextMessage):
        # if event.message.text == "test":
            # message_content = line_bot_api.get_message_content(event.message.id)
            # Pic_Name = line_bot_api.get_message_content(event.message.text)
            # print('Pic_Name before function:' + Pic_Name)
            # UploadToImgur(Pic_Name)
            
            
    # elif isinstance(event.message, VideoMessage):
        # ext = 'mp4'
    # elif isinstance(event.message, AudioMessage):
        # ext = 'm4a'
    # elif isinstance(event.message, TextMessage):
        # if event.message.text == "看看大家都傳了什麼圖片":
            # client = ImgurClient(client_id, client_secret)
            # images = client.get_album_images(album_id)
            # index = random.randint(0, len(images) - 1)
            # url = images[index].link
            # image_message = ImageSendMessage(
                # original_content_url=url,
                # preview_image_url=url
            # )
            # line_bot_api.reply_message(
                # event.reply_token, image_message)
            # return 0
        # else:
            # line_bot_api.reply_message(
                # event.reply_token, [
                    # TextSendMessage(text=' yoyo'),
                    # TextSendMessage(text='請傳一張圖片給我')
                # ])
            # return 0
            

            
if __name__ == "__main__":
    app.run()