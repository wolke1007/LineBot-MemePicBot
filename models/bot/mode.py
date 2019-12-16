# -*- coding: utf-8 -*-
from config import *
from ..ORM import PicInfo, System, UserInfo, Session


class Mode():

    def __get_system_config(self, raw_system_config, group_id):
        if raw_system_config:
            group_id_list = [i[0] for i in raw_system_config]
            index = group_id_list.index(group_id)
            # system_config[index] 會回傳一個 tuple 類似像 ('Cxxxxxx', 1, 1, 3)
            # 從左至右分別對應: group_id,	chat_mode, retrieve_pic_mode, trigger_chat
            #                        其中 chat_mode 的設定：0 = 不回圖
            #                                             1 = 隨機回所有 group 創的圖(預設)
            #                                             2 = 只回該 group 上傳的圖
            #                        其中 trigger_chat 預設為 3 個以上的字才回話，可以設為 2~15
            system_config = raw_system_config[index]
            return system_config
        else:
            return None

    def get_chat_mode(self, raw_system_config, group_id):
        print('enter get_chat_mode')
        if self.chat.event.message.text == '--mode':
            system_config = self.__get_system_config(raw_system_config, group_id)
            if system_config:
                self.reply_content = ("[當前模式為]\n" +
                                    "chat_mode:" +
                                    str(system_config[1]) + "\n"
                                    "retrieve_pic_mode:" +
                                    str(system_config[2]) + "\n"
                                    "trigger_chat:" +
                                    str(system_config[3])
                                    )
            else:
                self.reply_content = "尚無 mode 資料，請再試一次"
        else:
            pass

    # def choose_mode_action(self):
    #     print('self.chat.event.message.text == "--mode"')  # debug
    #     if self.chat.event.message.text[7:-2].strip(' ') == "trigger_chat":
    #         params_dict, update_pre_sql, self.reply_content \
    #             = self.set_trigger_chat(self.chat.event.message.text, group_id)
    #         if update_pre_sql:
    #             dbm.iud_from_db(update_pre_sql, params_dict)
    #         reply_msg(
    #             self.chat.event.reply_token,
    #             self.reply_content,
    #             content_type='text')
    #     elif self.chat.event.message.text[7:-2] == "chat_mode":
    #         params_dict, update_pre_sql, self.reply_content \
    #             = self.set_chat_mode(self.chat.event.message.text, group_id)
    #         if update_pre_sql:
    #             dbm.iud_from_db(update_pre_sql, params_dict)
    #         reply_msg(
    #             self.chat.event.reply_token,
    #             self.reply_content,
    #             content_type='text')
    #     else:
    #         select_pre_sql = (
    #             "SELECT * FROM system WHERE group_id = :group_id")
    #         raw_system_config = dbm.select_from_db(
    #             select_pre_sql, params_dict={
    #                 'group_id': group_id})
    #         print('raw_system_config', raw_system_config)  # debug
    #         self.reply_content = self.__get_mode_status(raw_system_config, group_id)
    #         reply_msg(
    #             self.chat.event.reply_token,
    #             self.reply_content,
    #             content_type='text')

    def set_trigger_chat(self):
        # --mode trigger_chat 1
        if self.chat.event.message.text[:20] == '--mode trigger_chat ':
            try:
                threshold = int(self.chat.event.message.text[-2:].strip(' '))
            except ValueError:
                self.reply_content = ("trigger_chat 後需設定介於 2~15 的數字"
                                "，如 --mode trigger_chat 15")
                params_dict, pre_sql = None, None
            # 不允許使用者設置低於 2 或是大於 15 個字元，於 config.py 中設定
            if threshold < PIC_NAME_LOW_LIMIT or threshold > PIC_NAME_HIGH_LIMIT:
                self.reply_content = ("trigger_chat 後需設定介於 2~15 的數字，"
                                "如 --mode trigger_chat 15")
                params_dict, pre_sql = None, None
            else:
                params_dict = {
                    'group_id': self.chat.event.source.group_id,
                    'trigger_chat': threshold
                }
                update_pre_sql = ("UPDATE system SET trigger_chat=:trigger_chat "
                                "WHERE group_id=:group_id")
                self.reply_content = '更改 trigger_chat 為 ' + str(threshold)
            self.reply_msg(
                    self.chat.event.reply_token,
                    self.reply_content,
                    content_type='text')
        else:
            pass

    def set_chat_mode(self):
        '''
        --mode chat_mode 0~2
        0 = 不回圖
        1 = 隨機回所有群組創的圖(預設)
        2 = 只回該群組上傳的圖
        '''
        if self.chat.event.message.text[:17] != '--mode chat_mode ':
            try:
                chat_mode = int(self.chat.event.message.text[-1])
                if chat_mode not in [0, 1, 2]:
                    self.reply_content = ("chat_mode 後需設定介於 0~2 的數字，"
                                    "如 --mode chat_mode 2")
                    params_dict, pre_sql = None, None
                else:
                    self.reply_content = '更改 chat_mode 為 ' + str(chat_mode)
            except ValueError:
                self.reply_content = ("chat_mode 後需設定介於 0~2 的數字，"
                                "如 --mode chat_mode 2")
                params_dict, pre_sql = None, None
            params_dict = {'group_id': self.chat.event.source.group_id,
                        'chat_mode': chat_mode}
            update_pre_sql = ("UPDATE system SET chat_mode=:chat_mode "
                            "WHERE group_id=:group_id")
            self.reply_msg(
                self.chat.event.reply_token,
                self.reply_content,
                content_type='text')
        else:
            pass


if __name__ == '__main__':
    pass
