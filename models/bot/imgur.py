# -*- coding: utf-8 -*-
from config import *
# from config_for_test import *  # debug
from json import loads
from requests import post
from base64 import b64encode
from imgur_auth import ImgurClient
from ..ORM import PicInfo, System, UserInfo, Session


class Imgur():

    def _upload_to_imgur(self, payload, pic_name):
        try:
            data = {
                'image': payload,
                'album': ALBUM_ID,
                'name': pic_name,
                'title': pic_name,
                'description': 'Upload From MemePicLineBot'
            }
            # 這邊要考慮在 description 中加入 sha256 加密過的使用者 line user id
            # 來達到嚇阻避免使用者濫用，濫用情況類似像是 PO 違法照片等等
            # 也要想方法公告表示不要將個人資料與非法照片上傳（類似裸照或是未成年照片等等，我不想被ＦＢＩ抓．．．）否則將依法究辦之類的
            # 但目前不確定 user_id 是不是一段時間就會換，是不是非 unique..
            InstanceClient = ImgurClient(CLIENT_ID, CLIENT_SECRET,
                                        ACCESS_TOKEN, REFRESH_TOKEN)
            headers = InstanceClient.prepare_headers()
            response = post('https://api.imgur.com/3/image', headers=headers, data=data)
            pic_link = loads(response.text)['data']['link']
            session.query(PicInfo)\
                .filter(PicInfo.user_id == self.chat.event.source.user_id)\
                .filter(PicInfo.group_id == self.chat.group_id)\
                .filter(PicInfo.pic_name == pic_name)\
                .update({PicInfo.pic_link: pic_link})
            session.commit()
            self.reply_content = pic_link
        except Exception as e:
            print('upload_to_imgur Exception e:', e)
            self.reply_content = False
        finally:
            return self.reply_content

    def upload_to_imgur_with_image(self):
        if self.chat.is_image_event:
            session = Session()
            had_named_pic_with_NULL_link = session.query(PicInfo)\
                .filter(PicInfo.user_id == self.chat.event.source.user_id)\
                .filter(PicInfo.group_id == self.chat.group_id)\
                .filter(PicInfo.pic_link == 'NULL').all()
            if had_named_pic_with_NULL_link:
                payload = b64encode(self.chat.binary_pic)
                pic_name = had_named_pic_with_NULL_link[0].pic_name
                self._upload_to_imgur(payload, pic_name)
                self.reply_content = '上傳成功' if self.reply_content else '上傳失敗'
                self._reply_msg(
                        content_type='text',
                        function_name=self.upload_to_imgur_with_image.__name__)
        else:
            pass

    def upload_to_imgur_with_link(self):
        if self.chat.is_image_event == False and \
            (self.chat.event.message.text[:4] == "http" and
             self.chat.event.message.text[:5] == "https") and \
            (self.chat.event.message.text[-4:] == ".jpg" or \
             self.chat.event.message.text[-5:] == ".jpeg" or \
             self.chat.event.message.text[-4:] == ".png" or \
             self.chat.event.message.text[-4:] == ".gif"):
            session = Session()
            had_named_pic_with_NULL_link = session.query(PicInfo)\
                .filter(PicInfo.user_id == self.chat.event.source.user_id)\
                .filter(PicInfo.group_id == self.chat.group_id)\
                .filter(PicInfo.pic_link == 'NULL').all()
            session.close()
            if had_named_pic_with_NULL_link:
                pic_name = had_named_pic_with_NULL_link[0].pic_name
                payload = self.chat.event.message.text
                self._upload_to_imgur(payload, pic_name)
                self.reply_content = '上傳成功' if self.reply_content else '上傳失敗'
                self._reply_msg(
                        content_type='text',
                        function_name=self.upload_to_imgur_with_link.__name__)
            else:
                pass


if __name__ == '__main__':
    pass
