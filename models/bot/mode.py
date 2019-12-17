# -*- coding: utf-8 -*-
from config import *
# from config_for_test import *  # debug
from ..ORM import PicInfo, System, UserInfo, Session


class Mode():

    def get_chat_mode(self):
        if self.is_image_event:
            return
        if self.chat.event.message.text == '--mode':
            self.reply_content = ("[當前模式為]\n" +
                                  "chat_mode:" +
                                  str(self.chat.chat_mode) + "\n"
                                  "retrieve_pic_mode:" +
                                  str(self.chat.retrieve_pic_mode) + "\n"
                                  "trigger_chat:" +
                                  str(self.chat.trigger_chat)
                                  )
            self._reply_msg(
                    content_type='text',
                    function_name=self.get_chat_mode.__name__)
        else:
            pass

    def set_trigger_chat(self):
        if self.is_image_event:
            return
        if self.chat.event.message.text[:20] == '--mode trigger_chat ':
            try:
                threshold = int(self.chat.event.message.text[-2:].strip(' '))
                # 不允許使用者設置低於 2 或是大於 15 個字元，於 config.py 中設定
                if threshold >= PIC_NAME_LOW_LIMIT and threshold <= PIC_NAME_HIGH_LIMIT:
                    session = Session()
                    session.query(System.trigger_chat).filter(System.group_id == self.chat.group_id).update({System.trigger_chat: threshold})
                    session.commit()
                    session.close()
                    self.reply_content = '更改 trigger_chat 為 ' + str(threshold)
                else:
                    raise ValueError
            except ValueError:
                self.reply_content = ("trigger_chat 後需設定介於 2~15 的數字"
                                      "，如 --mode trigger_chat 15")
            finally:
                self._reply_msg(
                    content_type='text',
                    function_name=self.set_trigger_chat.__name__)
        else:
            pass

    def set_chat_mode(self):
        '''
        --mode chat_mode 0~2
        0 = 不回圖
        1 = 隨機回所有群組創的圖(預設)
        2 = 只回該群組上傳的圖
        '''
        if self.is_image_event:
            return
        if self.chat.event.message.text[:17] == '--mode chat_mode ':
            try:
                chat_mode = int(self.chat.event.message.text[-1])
                if chat_mode not in [0, 1, 2]:
                    self.reply_content = ("chat_mode 後需設定介於 0~2 的數字，"
                                          "如 --mode chat_mode 2")
                else:
                    session = Session()
                    res = session.query(System.chat_mode).filter(System.group_id == self.chat.group_id).update({System.chat_mode: chat_mode})
                    session.commit()
                    session.close()
                    self.reply_content = '更改 chat_mode 為 ' + str(chat_mode)
            except ValueError:
                self.reply_content = ("chat_mode 後需設定介於 0~2 的數字，"
                                      "如 --mode chat_mode 2")
            finally:
                self._reply_msg(
                    content_type='text',
                    function_name=self.set_chat_mode.__name__)
        else:
            pass


if __name__ == '__main__':
    pass
