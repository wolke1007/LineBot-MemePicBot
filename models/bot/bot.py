# -*- coding: utf-8 -*-
from config import *
# from pandas import DataFrame
# from numpy import array
# from matplotlib.pyplot import subplots
from io import BytesIO
from six import iteritems
# from PIL import Image
# from matplotlib.font_manager import FontProperties
from .skill import Skill
from .mode import Mode
from ..ORM import PicInfo, System, UserInfo, Session
import os


class Bot(Skill, Mode):

    def __init__(self, chat):
        self.known_skills = {'#upload_to_imgur#': self.upload_to_imgur,
                             '--help': self.get_help,
                             '--list': self.reply_pic_name_list,
                             '--delete': self.delete_pic}
        self.known_modes = {'--mode': self.get_chat_mode,
                            '--mode trigger_chat': self.set_trigger_chat,
                            '--mode chat_mode': self.set_chat_mode}
        self.chat = chat
        self.reply_content = None # this is for debug, that can print reply content
        self.do_all_skills()
        self.do_all_modes()

    def do_all_skills(self):
        '''
        將所有的 Skill method 輪巡過一遍，執行所有不為 private 的功能
        是否符合執行的條件則在各 skill 中判斷
        '''
        for method in dir(Skill):
            if '__' not in method:
                eval('self.'+str(method)+'()')

    def do_all_modes(self):
        '''
        將所有的 Mode method 輪巡過一遍，執行所有不為 private 的功能
        是否符合執行的條件則在各 mode 中判斷
        '''
        for method in dir(Mode):
            if '__' not in method:
                eval('self.'+str(method)+'()')

    # def do_skill_or_set_mode(self):
    #     '''
    #     Bot 拿來判斷聊天的內容是否要任何事情
    #     並在 skill or mode 的 class 中實作
    #     '''
    #     print('enter do skill')
    #     chat_text = self.chat.event.message.text
    #     print('chat_text: ', chat_text)
    #     do_skill = self.known_skills.get(chat_text) if chat_text in self.known_skills else None
    #     do_mode = self.known_modes.get(chat_text) if chat_text in self.known_modes else None
    #     if chat_text[:-2] in self.known_skills:
    #         do_skill = self.known_skills.get(chat_text[:-2])
    #     elif chat_text[:-2] in self.known_modes:
    #         do_mode = self.known_modes.get(chat_text[:-2])
    #     elif chat_text[0] == '#' and chat_text[-1] == '#':
    #         self.pic_name = chat_text[1:-1]
    #         do_skill = self.known_skills.get('#upload_to_imgur#')
    #     if do_skill:
    #         do_skill()
    #     if do_mode:
    #         do_mode()


if __name__ == '__main__':
    pass
