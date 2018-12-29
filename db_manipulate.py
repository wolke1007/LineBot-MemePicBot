# -*- coding: utf-8 -*-
from config import *
import pymysql
from sqlalchemy import text
from sqlalchemy import create_engine

engine = create_engine(USER_INFO_CONNECT)


class DBManipulate():
    def __init__(self, pre_sql, params_dict):
        self.pre_sql = pre_sql
        self.select_params_dict = params_dict
        self.insert_params_dict = params_dict
        self.update_params_dict = params_dict

    @classmethod
    def select_from_db(self):
        bind_sql = text(self.pre_sql)
        with engine.connect() as conn:
            try:
                resproxy = conn.execute(bind_sql, self.select_params_dict)
                rows = resproxy.fetchall()
                ret = rows
                return ret
            except DatabaseError:
                return False

    @classmethod
    def insert_from_db(self):
        bind_sql = text(self.pre_sql)
        with engine.connect() as conn:
            try:
                resproxy = conn.execute(self.bind_sql, self.insert_params_dict)
                return True
            except DatabaseError:
                return False

    @classmethod
    def update_from_db(self):
        bind_sql = text(self.pre_sql)
        with engine.connect() as conn:
            try:
                resproxy = conn.execute(self.bind_sql, self.update_params_dict)
                return True
            except DatabaseError:
                return False

# SQL 參考：
# 1. https://www.jianshu.com/p/e6bba189fcbd
# 2. https://blog.csdn.net/slvher/article/details/47154363
