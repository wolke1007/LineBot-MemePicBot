# -*- coding: utf-8 -*-
from config import *
import pymysql
from sqlalchemy import text
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

engine = create_engine(USER_INFO_CONNECT)


class DBManipulate():
    @staticmethod
    def select_from_db(pre_sql, params_dict):
        bind_sql = text(pre_sql)
        with engine.connect() as conn:
            try:
                resproxy = conn.execute(bind_sql, params_dict)
                rows = resproxy.fetchall()
                ret = rows
                return ret
            except SQLAlchemyError:
                return False

    @staticmethod
    def insert_from_db(pre_sql, params_dict):
        bind_sql = text(pre_sql)
        with engine.connect() as conn:
            try:
                resproxy = conn.execute(bind_sql, params_dict)
                return True
            except SQLAlchemyError:
                return False

    @staticmethod
    def update_from_db(pre_sql, params_dict):
        bind_sql = text(pre_sql)
        with engine.connect() as conn:
            try:
                resproxy = conn.execute(bind_sql, params_dict)
                return True
            except SQLAlchemyError:
                return False

    @staticmethod
    def delete_from_db(pre_sql, params_dict):
        bind_sql = text(pre_sql)
        with engine.connect() as conn:
            try:
                resproxy = conn.execute(bind_sql, params_dict)
                return True
            except SQLAlchemyError:
                return False


if __name__ == '__main__':
    pass
# SQL 參考：
# 1. https://www.jianshu.com/p/e6bba189fcbd
# 2. https://blog.csdn.net/slvher/article/details/47154363
