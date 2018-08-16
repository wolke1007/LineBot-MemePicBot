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

line_channel_access_token = 'FxI3Qlfn3Mwyne/OujcIsYfOQCcIOZTUIYbDF2d41/GZAlQv2p5FGkp/ategG6xe0ErAsJCQOeHxdSM1xJ7uCejar1IGM5tDCzSFp40QmWs0BEjVec2nkacPIrL8Hh8XVvBxUgEUsGG6U+nvyGRClgdB04t89/1O/w1cDnyilFU='
line_channel_secret = '7c2930cb70180aae136f76504fba88bd'
client_id = 'ef420e58e8af248'
client_secret = '461a057a65611590954d7692f78964920b484929'
album_id = 'UxgXZbe'
access_token = 'YOUR_IMGUR_ACCESS_TOKEN'
refresh_token = 'YOUR_IMGUR_ACCESS_TOKEN'

# line_bot_api = LineBotApi()
# handler = WebhookHandler('')
# imgur_client_id = ef420e58e8af248
# imgur_client_secret = 461a057a65611590954d7692f78964920b484929	
# imgur_album_id = UxgXZbe
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
    if isinstance(event.message, ImageMessage):
        print('enter image part') #Debug log
        ext = 'jpg'
        message_content = line_bot_api.get_message_content(event.message.id)
        # with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
        with tempfile.NamedTemporaryFile(prefix=ext + '-', delete=False) as tf:
            for chunk in message_content.iter_content():
                tf.write(chunk)
            tempfile_path = tf.name
        print(os.getcwd()) #Debug log
        dist_path = tempfile_path + '.jpg'
        dist_name = os.path.basename(dist_path)
        os.rename(tempfile_path, dist_path)
        from imgurpython.helpers.error import ImgurClientError
        try:
            # this part is from imgurpython Document
            client = ImgurClient(client_id, client_secret)
            authorization_url = client.get_auth_url('pin')
            credentials = client.authorize('PIN OBTAINED FROM AUTHORIZATION', 'pin')
            client.set_user_auth(credentials['access_token'], credentials['refresh_token'])
            # ######################################
            config = {
                'album': album_id,
                'name': 'Catastrophe!',
                'title': 'Catastrophe!',
                'description': 'Cute kitten being cute on '
            }
            # path = os.path.join('static', 'tmp', dist_name)
            path = dist_name
            client.upload_from_path(path, config=config, anon=False)
            print('before remove: '+os.getcwd()) #Debug log
            os.remove(path)
            print('after remove: '+os.getcwd()) #Debug log
            print(path)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='上傳成功'))
        except ImgurClientError as e:
            print(e.error_message)
            print(e.status_code)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='上傳失敗'))
        return 0

    elif isinstance(event.message, VideoMessage):
        ext = 'mp4'
    elif isinstance(event.message, AudioMessage):
        ext = 'm4a'
    elif isinstance(event.message, TextMessage):
        if event.message.text == "看看大家都傳了什麼圖片":
            client = ImgurClient(client_id, client_secret)
            images = client.get_album_images(album_id)
            index = random.randint(0, len(images) - 1)
            url = images[index].link
            image_message = ImageSendMessage(
                original_content_url=url,
                preview_image_url=url
            )
            line_bot_api.reply_message(
                event.reply_token, image_message)
            return 0
        else:
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage(text=' yoyo'),
                    TextSendMessage(text='請傳一張圖片給我')
                    print(os.getcwd()) #Debug log
                ])
            return 0

if __name__ == "__main__":
    app.run()