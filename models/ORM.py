# -*- coding: utf-8 -*-
from config import *
# from config_for_test import *  # debug
import pymysql
from sqlalchemy import create_engine, Table, MetaData, Column, String, Integer, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


engine = create_engine(CONNECTION_INFO, echo=False) # echo 為 debug 資訊
Base = declarative_base()
Session  = sessionmaker(bind=engine)


class PicInfo(Base):
    __tablename__ = 'pic_info'
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(String, nullable=False)
    pic_name = Column(String, nullable=False)
    pic_link = Column(String, nullable=False)
    created_time = Column(String, nullable=False)
    group_id = Column(String, nullable=True)


class System(Base):
    __tablename__ = 'system'
    chat_mode = Column(Integer, nullable=False)
    retrieve_pic_mode = Column(Integer, nullable=False)
    trigger_chat = Column(Integer, nullable=False)
    group_id = Column(String, primary_key=True, nullable=True)


class UserInfo(Base):
    __tablename__ = 'user_info'
    user_id = Column(String, primary_key=True, nullable=True)
    banned = Column(Integer, nullable=False)
    account_created_time = Column(String, nullable=True)


if __name__ == '__main__':
    pass

# SQL 參考：
# 1. https://www.jianshu.com/p/e6bba189fcbd
# 2. https://blog.csdn.net/slvher/article/details/47154363
# 3. https://docs.sqlalchemy.org/en/13/orm/query.html