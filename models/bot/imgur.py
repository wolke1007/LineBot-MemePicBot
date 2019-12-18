# -*- coding: utf-8 -*-
from config import *
from json import loads
from requests import post
from base64 import b64encode
from imgur_auth import ImgurClient
from ..ORM import PicInfo, System, UserInfo, Session


# 上傳圖片這邊有兩種做法，可行性上在後面討論
# 1. 先上傳圖片，後命名剛剛圖片的名稱
# 2. 先命名圖片名稱，後上傳圖片
# ~~~~~~先講結論~~~~~ 最後決定採用 2，也就是採取先命名後上傳
# 探討幾種 1 的實作方式以及我覺得不適用原因:
# 1. 將圖片暫存在 memory 於命名後拿來上傳，但因為線上會起多個 thread 跑程式有機會是另一個 thread 去詢問而拿不到圖片
#    另外也可能會有 memory 不足的問題
# 2. 有考慮用寫檔方式儲存暫存檔，但 Google Cloud Function 不支援寫檔操作所以無法
# 3. 先存圖片到 DB 之後命名並上傳，但這將會增加 DB Server 傳輸負擔跟流量成本
# 4. 只要收到圖片一律上傳，如果仍未命名但又有收到圖片，就刪除前一張後再上傳，直到有命名則修改最後一張上傳圖片的名稱為正式名稱
#    但這會增加上傳的成本，依據 Imgur 免費的流量只能上傳 10,000 張圖片每月，就算花 25 鎂也是 60,000 每月，並不能這樣玩
# 最後決定，只能確認使用者有先命名完才做上傳動作，確保每一次有確定要上傳才做
# 與此同時，有考慮每個人是不是要設定 quota 來限制是不是一天只能上傳幾張圖片(目前沒此設計)
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
            self.reply_content = pic_link
        except Exception as e:
            print('upload_to_imgur Exception e:', e)
            self.reply_content = False
        finally:
            return self.reply_content
    
    def __upload_to_imgur_with(self, payload_type, function_name):
        session = Session()
        had_named_pic_with_NULL_link = session.query(PicInfo)\
            .filter(PicInfo.user_id == self.chat.event.source.user_id)\
            .filter(PicInfo.group_id == self.chat.group_id)\
            .filter(PicInfo.pic_link == 'NULL')
        if had_named_pic_with_NULL_link.all():
            payload = b64encode(self.chat.binary_pic) if payload_type == 'image' else self.chat.event.message.text
            pic_name = had_named_pic_with_NULL_link[0].pic_name
            upload_result = self._upload_to_imgur(payload, pic_name)
            if upload_result:
                pic_link = upload_result
                had_named_pic_with_NULL_link.update({PicInfo.pic_link: pic_link})
                session.commit()
                self.reply_content = '上傳成功'
            else:
                self.reply_content = '上傳失敗'
            self._reply_msg(
                content_type='text',
                function_name=function_name)
        session.close()

    def upload_to_imgur_with_image(self):
        if self.chat.is_image_event:
            self.__upload_to_imgur_with('image', self.upload_to_imgur_with_image.__name__)
        else:
            pass

    def upload_to_imgur_with_link(self):
        if self.chat.is_image_event == False and \
            (self.chat.event.message.text[:4] == "http" or
             self.chat.event.message.text[:5] == "https") and \
            (self.chat.event.message.text[-4:] == ".jpg" or \
             self.chat.event.message.text[-5:] == ".jpeg" or \
             self.chat.event.message.text[-4:] == ".png" or \
             self.chat.event.message.text[-4:] == ".gif"):
            self.__upload_to_imgur_with('link', self.upload_to_imgur_with_link.__name__)
        else:
            pass


if __name__ == '__main__':
    pass
