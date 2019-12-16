# -*- coding: utf-8 -*-
from json import loads
from requests import post
from ..ORM import PicInfo, System, UserInfo, Session


class Imgur():

    def upload_to_imgur(self):
        # 因為會覆寫，所以直接再 Add 一次不用刪除，且統一用小寫儲存
        # 圖片名稱長度在此設定門檻，目前設定為 3~15 個字
        if self.chat.pic_name:
            self.chat.pic_name = self.chat.pic_name.lower()
            if len(self.chat.pic_name) >= self.chat.pic_name_LOW_LIMIT and \
            len(self.chat.pic_name) <= self.chat.pic_name_HIGH_LIMIT:
                if self.is_filename_exist:
                    # 如果圖片重複了，對 user_id pic_link 欄位進行 update
                    print('圖片已經存在，更新 user_id pic_link')
                    session = Session()
                    session.query(PicInfo).filter(PicInfo.pic_name == self.chat.pic_name).all()
                    params_dict = {
                        'user_id': user_id,
                        'pic_name': self.chat.pic_name,
                        'group_id': group_id
                    }
                    update_pre_sql = ("UPDATE pic_info SET user_id=:user_id, pic_link=NULL "
                                        "WHERE self.chat.pic_name=:self.chat.pic_name AND group_id=:group_id")
                    res = dbm.iud_from_db(update_pre_sql, params_dict)
                    print('user_id pic_link 已經淨空，準備接收新圖片')
                else:
                    # 如果沒重複直接 insert
                    print('新增 user_id self.chat.pic_name')
                    params_dict = {
                        'user_id': user_id,
                        'pic_name': self.chat.pic_name,
                        'group_id': group_id
                    }
                    insert_pre_sql = ("INSERT INTO pic_info (user_id, self.chat.pic_name, group_id)"
                                        "values (:user_id, :self.chat.pic_name, :group_id)")
                    res = dbm.iud_from_db(insert_pre_sql, params_dict)
                    print('user_id self.chat.pic_name 已經新增，準備接收新圖片')
                if res is True:
                    line_reply_msg(
                        event.reply_token,
                        '圖片名稱已設定完畢，請上傳圖片',
                        content_type='text')
                else:
                    line_reply_msg(
                        event.reply_token,
                        'Database 寫檔失敗！請聯絡管理員',
                        content_type='text')
            else:
                line_reply_msg(
                    event.reply_token,
                    '圖片名稱長度需介於 3~10 個字（中英文或數字皆可)',
                    content_type='text')
                return

            if event.message.text[:4] == "http" and (event.message.text[-4:] == ".jpg" or
                                                        event.message.text[-4:] == ".jpeg" or
                                                        event.message.text[-4:] == ".png" or
                                                        event.message.text[-4:] == ".gif"):
                params_dict = {
                    'user_id': user_id,
                    'group_id': group_id
                }
                # 名字設定好但還沒有 pic_link 的就是準備要上傳的
                # (只抓 user_id 符合的是為了避免設定名字後別人幫你上傳圖片的問題)
                select_pre_sql = ("SELECT self.chat.pic_name FROM pic_info "
                                    "WHERE pic_link IS NULL AND user_id=:user_id "
                                    "AND group_id=:group_id")
                # 回傳為 list type 裡面包著 tuple 預期一定會拿到 self.chat.pic_name 所以直接取第一個不怕噴錯
                self.chat.pic_name = dbm.select_from_db(select_pre_sql, params_dict)
                self.chat.pic_name = self.chat.pic_name[0][0] if self.chat.pic_name else None
                if is_filename_exist(self.chat.pic_name, group_id):
                    print('name already exist, start to upload')
                    pic_link, reply_msg = upload_to_imgur(
                        self.chat.pic_name, url=event.message.text)
                    params_dict = {
                        'user_id': user_id,
                        'pic_link': pic_link,
                        'group_id': group_id
                    }
                    # 名字設定好但還沒有 pic_link 的且 user_id 符合的就是剛上傳好的
                    update_pre_sql = ("UPDATE pic_info SET pic_link=:pic_link, group_id=:group_id "
                                        "WHERE user_id=:user_id AND pic_link IS NULL")
                    dbm.iud_from_db(update_pre_sql, params_dict)
                    line_reply_msg(
                        event.reply_token,
                        reply_msg,
                        content_type='text')
            
            
            
            
            
            
            print('enter upload_to_imgur')
            try:
                payload = b64encode(binary_pic) if binary_pic else url
                print('type(payload)', type(payload))
                data = {
                    'image': payload,
                    'album': ALBUM_ID,
                    'name': self.chat.pic_name,
                    'title': self.chat.pic_name,
                    'description': 'Upload From MemePicLineBot'
                }
                # 這邊要考慮在 description 中加入 sha256 加密過的使用者 line user id
                # 來達到嚇阻避免使用者濫用，濫用情況類似像是 PO 違法照片等等
                # 也要想方法公告表示不要將個人資料與非法照片上傳（類似裸照或是未成年照片等等，我不想被ＦＢＩ抓．．．）否則將依法究辦之類的
                InstanceClient = ImgurClient(CLIENT_ID, CLIENT_SECRET,
                                            ACCESS_TOKEN, REFRESH_TOKEN)
                headers = InstanceClient.prepare_headers()
                response = post('https://api.imgur.com/3/image',
                                        headers=headers, data=data)
                pic_link = loads(response.text)['data']['link']
                reply_msg = '上傳成功'
                return pic_link, reply_msg
            except Exception as e:
                print('upload_to_imgur Exception e:', e)
                reply_msg = '上傳失敗，請聯絡管理員'
                return '', reply_msg


if __name__ == '__main__':
    pass
