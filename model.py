# -*- coding: utf-8 -*-
from config import *
import pymysql
from sqlalchemy import create_engine, Table, MetaData, Column, String, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


engine = create_engine(CONNECTION_INFO, echo=True)
Base = declarative_base()
Session  = sessionmaker(bind=engine)


# for ORM use
class PicInfo(Base):
    __tablename__ = 'pic_info'
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(String, nullable=False)
    pic_name = Column(String, nullable=False)
    pic_link = Column(String, nullable=False)
    created_time = Column(String, nullable=False)
    group_id = Column(String, nullable=True)


# for ORM use
class System(Base):
    __tablename__ = 'system'
    chat_mode = Column(Integer, nullable=False)
    retrieve_pic_mode = Column(Integer, nullable=False)
    trigger_chat = Column(Integer, nullable=False)
    group_id = Column(String, primary_key=True, nullable=True)


# for ORM use
class UserInfo(Base):
    __tablename__ = 'user_info'
    user_id = Column(String, primary_key=True, nullable=True)
    banned = Column(Integer, nullable=False)
    account_created_time = Column(String, nullable=True)


class Chat():

    def __init__(self, event):
        self.user_id = event.source.user_id
        try:
            self.group_id = event.source.group_id
        except AttributeError as e:
            self.group_id = 'NULL'
            print("send from 1 to 1 chat room, so there's no group id")
        self.message_id = event.message.id
        self.is_user_id_banned = self.__is_user_id_banned(self.user_id)

    def __is_user_id_banned(self, user_id):
        chat_user = UserInfo(user_id=self.user_id)
        session = Session()
        ret = session.query(UserInfo).filter(UserInfo.user_id == chat_user.user_id)
        session.close()
        print('ret[0].banned: ', ret[0].banned)
        return True if ret[0].banned == 1 else False

    # def __add_user_id_if_not_exist(user_id):
    #     print('enter add_userid_if_not_exist')
    #     params_dict = {
    #         'user_id': user_id
    #     }
    #     select_pre_sql = ("SELECT user_id FROM user_info WHERE user_id=:user_id")
    #     res = dbm.select_from_db(select_pre_sql, params_dict)
    #     # 回傳值應為 list type 裡面包著 tuple，但有可能沒有值所以不指定取第一個
    #     if res:
    #         # user_id 存在，不做事
    #         return
    #     else:
    #         # user_id 不存在，加入
    #         params_dict = {
    #             'user_id': user_id,
    #             'banned': 0
    #         }
    #         insert_pre_sql = ("INSERT INTO user_info (user_id, banned) "
    #                         "VALUES (:user_id, :banned)")
    #         dbm.iud_from_db(insert_pre_sql, params_dict)
    #         return True

    def is_filename_exist(pic_name, group_id):
        print('enter is_filename_exist')
        if not pic_name:
            return False
        params_dict = {
            'pic_name': pic_name,
            'group_id': group_id,
        }
        select_pre_sql = ("SELECT pic_name FROM pic_info WHERE "
                        "pic_name=:pic_name AND group_id=:group_id")
        # 有設定圖片名稱，但是還沒上傳所以沒有 pic_link
        res = dbm.select_from_db(select_pre_sql, params_dict)
        return True if res else False


# class DBManipulate():
#     @staticmethod
#     def select_from_db(pre_sql, params_dict):
#         bind_sql = text(pre_sql)
#         with engine.connect() as conn:
#             try:
#                 resproxy = conn.execute(bind_sql, params_dict)
#                 rows = resproxy.fetchall()
#                 ret = rows
#                 return ret
#             except SQLAlchemyError:
#                 return False

#     @staticmethod
#     def iud_from_db(pre_sql, params_dict):
#         # iud 代表 Insert Update Delete
#         bind_sql = text(pre_sql)
#         with engine.connect() as conn:
#             try:
#                 resproxy = conn.execute(bind_sql, params_dict)
#                 return True
#             except SQLAlchemyError:
#                 return False


if __name__ == '__main__':
    pass
# SQL 參考：
# 1. https://www.jianshu.com/p/e6bba189fcbd
# 2. https://blog.csdn.net/slvher/article/details/47154363
