# -*- coding: utf-8 -*-
from config import *
# from config_for_test import *  # debug
from .skill import Skill
from .mode import Mode
from ..ORM import PicInfo, System, UserInfo, Session
import os


class Bot(Skill, Mode):

    def __init__(self, chat, debug=False, echo=False):
        self.debug = debug
        self.echo = echo
        self.chat = chat
        if self.chat.user_banned:
            self.reply_content = 'user banned refuse to do skills or mode set'
            pass
        else:
            self.reply_content = None
            self.do_all_skills()
            self.do_all_modes()

    def do_all_skills(self):
        '''
        將所有的 Skill method 輪巡過一遍，執行所有不為 private 的功能
        是否符合執行的條件則在各 skill 中判斷
        '''
        for method in dir(Skill):
            if '__' not in method and method[0] != '_':
                eval('self.'+str(method)+'()')

    def do_all_modes(self):
        '''
        將所有的 Mode method 輪巡過一遍，執行所有不為 private 的功能
        是否符合執行的條件則在各 mode 中判斷
        '''
        for method in dir(Mode):
            if '__' not in method:
                eval('self.'+str(method)+'()')


if __name__ == '__main__':
    pass
