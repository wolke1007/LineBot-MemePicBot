# -*- coding: utf-8 -*-
from config import *
# from config_for_test import *  # debug
from .ORM import PicInfo, System, UserInfo, Session
from sqlalchemy.orm.exc import NoResultFound
from linebot import LineBotApi


line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)


class Chat():

    def __init__(self, event, is_image_event=None):
        self.event = event
        self.event.message.text = self.event.message.text.lower()
        # 統一使用小寫的文字做後續處理，儲存進 DB 與撈出來比對時都會是小寫，增加命中率
        # 若未來有考慮大小寫分開儲存則要改這邊
        self.is_image_event = is_image_event
        if self.is_image_event:
            self.binary_pic = line_bot_api.get_message_content(self.chat.event.message_id).content
        else:
            self.binary_pic = None
        try:
            self.group_id = event.source.group_id
        except AttributeError as e:
            self.group_id = 'NULL'
            print("send from 1 to 1 chat room, so there's no group id")
        self.add_user_id_if_not_exist()
        self.add_group_id_if_not_exist()
        self.user_banned,\
        self.chat_mode,\
        self.retrieve_pic_mode,\
        self.trigger_chat = self.get_chat_metadata()

    def add_user_id_if_not_exist(self):
        session = Session()
        try:
            session.query(UserInfo).filter(UserInfo.user_id == self.event.source.user_id).one()
        except NoResultFound:
            session.add(UserInfo(user_id=self.event.source.user_id, banned=0))
            session.commit()
        finally:
            session.close()

    def add_group_id_if_not_exist(self):
        session = Session()
        try:
            session.query(System).filter(System.group_id == self.group_id).one()
        except NoResultFound:
            session.add(System(group_id=self.group_id, chat_mode=1, retrieve_pic_mode=1, trigger_chat=3))
            session.commit()
        finally:
            session.close()

    def get_chat_metadata(self):
        '''
        檢查是否有已經設定的圖片名稱(ret2)需同時符合:
        1. 同個使用者 (避免 A 命名後，但上傳了 B 上傳的圖片)
        2. 同個聊天室 (避免在 A 聊天室命名，但上傳了 B 聊天室的圖片)
        3. 需只有 pic_name 存在，但 pic_link 為 NULL
        '''
        session = Session()
        ret = session.query(UserInfo, System)\
                    .filter(UserInfo.user_id == self.event.source.user_id)\
                    .filter(System.group_id == self.group_id)\
                    .one()

        # print('ret.UserInfo.banned: ', ret.UserInfo.banned,\
        #       'ret.System.chat_mode: ', ret.System.chat_mode,\
        #       'ret.System.retrieve_pic_mode: ', ret.System.retrieve_pic_mode,\
        #       'ret.System.trigger_chat: ', ret.System.trigger_chat)
        return ret.UserInfo.banned,\
               ret.System.chat_mode,\
               ret.System.retrieve_pic_mode,\
               ret.System.trigger_chat


if __name__ == '__main__':
    pass
# SQL 參考：
# 1. https://www.jianshu.com/p/e6bba189fcbd
# 2. https://blog.csdn.net/slvher/article/details/47154363
