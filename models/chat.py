# -*- coding: utf-8 -*-
from config import *
from .ORM import PicInfo, System, UserInfo, Session
from sqlalchemy.orm.exc import NoResultFound


class Chat():

    def __init__(self, event):
        self.event = event
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
        self.trigger_chat,\
        self.pic_name = self.get_chat_metadata()

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
            session.query(System).filter(System.group_id == self.event.source.group_id).one()
        except NoResultFound:
            session.add(System(group_id=self.event.source.group_id, chat_mode=1, retrieve_pic_mode=1, trigger_chat=3))
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
        ret1 = session.query(UserInfo, System)\
                    .filter(UserInfo.user_id == self.event.source.user_id)\
                    .filter(System.group_id == self.event.source.group_id)\
                    .one()
        # 有設定圖片名稱，但是還沒上傳所以沒有 pic_link
        ret2 = session.query(PicInfo)\
                    .filter(PicInfo.user_id == self.event.source.user_id)\
                    .filter(PicInfo.group_id == self.event.source.group_id)\
                    .filter(PicInfo.pic_link == 'NULL').all()
        ret2 = ret2.pic_name if ret2 else None
        session.close()
        print('ret1.UserInfo.banned: ', ret1.UserInfo.banned,\
              'ret1.System.chat_mode: ', ret1.System.chat_mode,\
              'ret1.System.retrieve_pic_mode: ', ret1.System.retrieve_pic_mode,\
              'ret1.System.trigger_chat: ', ret1.System.trigger_chat,\
              'ret2: ', ret2)
        return ret1.UserInfo.banned,\
               ret1.System.chat_mode,\
               ret1.System.retrieve_pic_mode,\
               ret1.System.trigger_chat,\
               ret2


if __name__ == '__main__':
    pass
# SQL 參考：
# 1. https://www.jianshu.com/p/e6bba189fcbd
# 2. https://blog.csdn.net/slvher/article/details/47154363
