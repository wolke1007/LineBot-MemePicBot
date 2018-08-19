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
global Pic_Name
Pic_Name = None
imgur_album_id = 'UxgXZbe'
app = Flask(__name__)
line_bot_api = LineBotApi(line_channel_access_token)
handler = WebhookHandler(line_channel_secret)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
    
    
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
    def GetPic():
        ext = 'jpg'
        message_content = line_bot_api.get_message_content(event.message.id)
        global User_ID_Who_Upload_Pic
        User_ID_Who_Upload_Pic = event.source.user_id
        with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
            for chunk in message_content.iter_content():
                tf.write(chunk)
            tempfile_path = tf.name
        print("tempfile_path before rename:" + tempfile_path) #debug
        dist_path = tempfile_path + '.' + ext
        # dist_path = Pic_Name + '.' + ext
        Dist_Name = os.path.basename(dist_path)
        os.rename(tempfile_path, dist_path)
        print("tempfile_path after rename:" + tempfile_path) #debug
        print("dist_path:" + dist_path) #debug
        print("Dist_Name:" + Dist_Name) #debug
        line_bot_api.push_message(
                event.source.group_id,
                TextSendMessage(text='圖片你想叫什麼名字?'))
        return Dist_Name, User_ID_Who_Upload_Pic

    # def GetPicName():
        # if isinstance(event.message, TextMessage):        
            # message_content = line_bot_api.get_message_content(event.message.id)
            # global Pic_Name
            # Pic_Name = event.message.text
        # print('Pic_Name: ')
        # print(Pic_Name)
        # return Pic_Name

    def UploadToImgur(dist_name, pic_name):
        try:
            print('UploadToImgur Pic_Name: ' + Pic_Name)
            client = ImgurClient(client_id, client_secret, access_token, refresh_token)
            config = {
                'album': imgur_album_id,
                'name': Pic_Name,
                'title': Pic_Name,
                'description': 'test description'
            }
            path = os.path.join('static', 'tmp', dist_name)
            print('path:'+path) #debug
            client.upload_from_path(path, config=config, anon=False)
            print(os.listdir(os.getcwd()+'/static/tmp')) #debug
            os.remove(path)  
            print(os.listdir(os.getcwd()+'/static/tmp')) #debug
            print(dir(event.source)) #debug
            print('event.source.group_id: ')  #debug
            print(event.source.group_id) #debug
            print(type(event.source.group_id)) #debug
            line_bot_api.push_message(
                event.source.group_id,
                TextSendMessage(text='上傳成功'))
        except Exception as e:
            print(e)
            line_bot_api.push_message(
                event.source.group_id,
                TextSendMessage(text='上傳失敗'))
# #################################################
#                   判斷式開始
# #################################################
    if isinstance(event.message, TextMessage):
        User_ID_Who_Set_Name = event.source.user_id
        print('User_ID_Who_Set_Name:') #debug
        print(User_ID_Who_Set_Name) #debug
        if event.message.text[0:1] == "!1" and User_ID_Who_Upload_Pic == User_ID_Who_Set_Name:
            Pic_Name = event.message.text[2:]

    elif isinstance(event.message, ImageMessage):
        if Pic_Name:
            print('Pic_Name exist do GetPic()') #debug
            Dist_Name, User_ID_Who_Upload_Pic = GetPic()
            print('User_ID_Who_Upload_Pic:') #debug
            print(User_ID_Who_Upload_Pic) #debug
            UploadToImgur(Dist_Name, Pic_Name)
            # Reset varible to None
            User_ID_Who_Set_Name = None
            User_ID_Who_Upload_Pic = None
        else:
            print('Pic_Name NOT exist do nothing') #debug
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage(text='沒有先設定名字，這張圖片將不被儲存')
                ])
            return 0
            
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