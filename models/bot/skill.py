# -*- coding: utf-8 -*-
from config import *
from config_for_test import *
# from pandas import DataFrame
# from numpy import array
# from matplotlib.pyplot import subplots
from io import BytesIO
from six import iteritems
# from PIL import Image
# from matplotlib.font_manager import FontProperties
from linebot import LineBotApi
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
from ..ORM import PicInfo, System, UserInfo, Session
from .imgur import Imgur
import re


line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)


class Skill(Imgur):

    def __reply_msg(self, to, content, content_type):
        '''
        1. 使用者主動敲 Bot，Bot 回覆人叫做 reply
        2. 這種需要 reply_token 才知道要回誰，
           且 reply_token 過一小段時間後會自動過期(或許是幾秒鐘後，沒文件明說)
           所以機器人不能太晚回話
        3. 可回文字 or 圖片
        '''
        if content_type is 'text':
            line_bot_api.reply_message(
                to,
                TextSendMessage(text=content))
        elif content_type is 'image':
            line_bot_api.reply_message(
                to,
                ImageSendMessage(preview_image_url=content,
                                 original_content_url=content))

    def __line_push_text_msg(to, content):
        '''
        1. Bot 主動敲人叫做 push，但有一定限制無法隨意敲 需另外研究
        2. 只能傳送文字
        '''
        line_bot_api.push_message(
            to,
            TextSendMessage(text=content))

    def __render_mpl_table(self, data, col_width=3.0, row_height=0.625, font_size=12,
                          header_color='#40466e', row_colors=['#f1f1f2', 'w'],
                          edge_color='w', bbox=[0, 0, 1, 1], header_columns=0,
                          ax=None, **kwargs):
        if ax is None:
            size = (array(data.shape[::-1]) + array([0, 1])) * \
                    array([col_width, row_height])
            fig, ax = subplots(figsize=size)
            ax.axis('off')
        # 取當前 main.py 的檔案位置，因為我上傳的字型檔跟它放一起
        from os import path
        dir_path = path.dirname(path.realpath(__file__))
        # STHeitiMedium.ttc 是中文字型檔，有了它 matplotlib 才有辦法印出中文，我擔心 GCP 沒有內建就自己上傳了
        font = FontProperties(fname=dir_path+"/STHeitiMedium.ttc", size=14)
        mpl_table = ax.table(cellText=data.values, bbox=bbox,
                             colLabels=data.columns, **kwargs)
        mpl_table.auto_set_font_size(False)
        mpl_table.set_fontsize(font_size)
        for k, cell in iteritems(mpl_table._cells):
            cell.set_edgecolor(edge_color)
            if k[0] == 0 or k[1] < header_columns:
                # fontproperties=font 這個是表格能不能印出中文的關鍵!
                cell.set_text_props(weight='bold', color='w',
                                    fontproperties=font)
                cell.set_facecolor(header_color)
            else:
                cell.set_facecolor(row_colors[k[0] % len(row_colors)])
                # fontproperties=font 這個是表格能不能印出中文的關鍵!
                cell.set_text_props(fontproperties=font)
        return ax

    def __turn_table_into_pic(self, table_object):
        print('enter turn_table_into_pic')
        pic = table_object
        plt_buf = BytesIO()
        pil_buf = BytesIO()
        pic.savefig(plt_buf, format='png')
        Image.open(plt_buf).save(pil_buf, format="png")
        plt_buf.close()
        byte_img = pil_buf.getvalue()
        pil_buf.close()
        return byte_img

    def __get_binary_pic(self, res):
        # res 格式為:  [('1',), ('ABC',)]
        res = [_[0] for _ in res]
        # 利用 set 將重複的字串給刪去
        res = list(set(res))
        # 字數從小到大排
        res.sort(key=lambda x: len(x))
        columns_cnt = 6
        # 取餘數用 None 補滿，讓每個 column 都有內容，pd.DataFrame 才不會變成只有一行
        res.extend([None for i in range(len(res) % columns_cnt)])
        # 將 list 包成 [[1,2,3], [1,2,3]] 這樣的格式再餵給 pd.DataFrame
        # (注意，裡面每個 list 一定要數量一致)
        res = [res[i:i + columns_cnt] for i in range(0, len(res), columns_cnt)]
        print('debug res[-1]:', res[-1])
        pd_res = DataFrame(res)
        table_object = self.__render_mpl_table(pd_res, header_columns=0,
                                                      col_width=2.0)
        table_object = table_object.get_figure()
        binary_pic = self.__turn_table_into_pic(table_object)
        return binary_pic

    def __del_pic(self, pic_name, group_id):
        print('enter del_pic')  # debug
        group_id = None if group_id == 'NULL' else group_id
        if group_id is None:
            print('group_id is NULL')
            params_dict = {
            'pic_name': pic_name,
            'group_id': 'NULL'
            }
            select_pre_sql = ("SELECT pic_name FROM pic_info "
                              "WHERE pic_name=:pic_name "
                              "AND group_id=:group_id")
            if not dbm.select_from_db(select_pre_sql, params_dict):
                return "沒有此圖片名稱"
            update_pre_sql = ("DELETE FROM pic_info "
                              "WHERE pic_name=:pic_name "
                              "AND group_id=:group_id")
            db_res = dbm.iud_from_db(update_pre_sql, params_dict)
            return "刪除非群組圖片名稱成功" if db_res else "刪除失敗"
        else:
            print('group_id is exist')
            params_dict = {
            'pic_name': pic_name,
            'group_id': group_id
            }
            select_pre_sql = ("SELECT pic_name FROM pic_info "
                              "WHERE pic_name=:pic_name "
                              "AND group_id=:group_id")
            if not dbm.select_from_db(select_pre_sql, params_dict):
                return "沒有此圖片名稱"
            update_pre_sql = ("DELETE FROM pic_info "
                              "WHERE pic_name=:pic_name "
                              "AND group_id=:group_id")
            db_res = dbm.iud_from_db(update_pre_sql, params_dict)
            return "刪除群組內的圖片名稱成功" if db_res else "刪除失敗"

    def get_help(self):
        if self.chat.event.message.text == '--help' or self.chat.event.message.text == '-h':
            help_content = (
                "貼心提醒您，請勿洩漏個資\n"
                "嚴 禁 上 傳 色 情 圖 片\n"
                "(作者: 我圖床不想被 banned 拜託配合ＱＡＱ\n"
                "\n"
                "[使用教學]\n"
                "  step 1. 設定圖片名稱，例如 #我是帥哥# (註1 2 3)\n"
                "  step 2. 上傳圖片或是貼上圖片的 URL，系統會回傳上傳成功 (註4)\n"
                "  step 3. 聊天時提到設定的圖片名稱便會觸發貼圖\n"
                "\n"
                "[聊天室設定教學]\n"
                "  --mode chat_mode 0~2\n"
                "    0 = 不回圖\n"
                "    1 = 隨機回所有群組創的圖(預設)\n"
                "    2 = 只回該群組上傳的圖\n"
                "  --mode trigger_chat 2~15\n"
                "    設定在此群組裡關鍵字超過幾字才回話，可以設為 2~15\n"
                "    e.g. trigger_chat 設為 3 的話，那 2 字的關鍵字就不會被觸發\n"
                "         關鍵字\"帥哥\"會在設定後就算聊天中提到也不會被觸發\n"
                "         但如果關鍵字為\"我是帥哥\"則不影響，因為超過 3 個字\n"
                "\n"
                "[其他功能]\n"
                "  --list 可以讓 BOT 回你現有圖片名稱的表格\n"
                "  --delete <圖片名稱>  刪除自己群組內的圖片名稱\n"
                "\n"
                "備註:\n"
                "  1. 圖片字數有限制，空白或是特殊符號皆算數\n"
                "  2. 設定同圖片名稱則會蓋掉前面上傳的\n"
                "  3. 如果設定多次名字再上傳圖片，則是多個關鍵字對應同一張圖片\n"
                "  4. 若上傳URL則必須為 http 開頭 .jpg .gif .png 結尾\n"
                "  5. 建議在 Line 設定將「自動下載照片」取消打勾\n"
                "    設定 > 照片。影片 > 自動下載照片\n"
            )  # line 手機版莫約 15 個中文字寬度就會換行，根據螢幕解析度有所增減
            self.reply_content = help_content
            self.__reply_msg(
                    self.chat.event.reply_token,
                    self.reply_content,
                    content_type='text')
        else:
            pass

    def delete_pic(self):
        if self.chat.event.message.text == '--delete':
            print('enter --delete')
            pic_name = self.chat.event.message.text[9:]
            pic_name = pic_name.lower()
            print('delete pic_name:', pic_name)
            if pic_name:
                reply_content = self.__del_pic(pic_name, self.chat.event.source.group_id)
                self.__reply_msg(
                    self.chat.event.reply_token,
                    reply_content,
                    content_type='text')
            else:
                reply_content = "範例: --delete <檔案名稱>"
                self.__reply_msg(
                    self.chat.event.reply_token,
                    reply_content,
                    content_type='text')
        else:
            pass

    def reply_pic_name_list(self):
        if self.chat.event.message.text == '--list':
            session = Session()
            # 撈出除了 pic_name_list 這張圖片以外的所有圖片名稱後做成表
            all_pic_info = session.query(PicInfo.pic_name, PicInfo.pic_link, PicInfo.group_id).filter(PicInfo.pic_name != 'pic_name_list').all()
            session.close()
            all_pic_name_in_db = [ pic.pic_name for pic in all_pic_info ]
            binary_pic = self.__get_binary_pic(all_pic_name_in_db)
            pic_link, reply_content = self.upload_to_imgur(
                                            pic_name='pic_name_list', binary_pic=binary_pic)
            if reply_content == '上傳成功':
                # 複寫名字為 'pic_name_list' 的 pic_link
                session = Session()
                session.query(PicInfo.pic_link).filter(PicInfo.pic_name == 'pic_name_list').update({PicInfo.pic_link: pic_link})
                session.commit()
                session.close()
                self.self.__reply_msg(
                    self.chat.event.reply_token,
                    pic_link,
                    content_type='image')
            else:
                self.self.__reply_msg(
                    self.chat.event.reply_token,
                    reply_content,
                    content_type='text')
        else:
            pass

    def send_pic_back(self):
        if self.chat.chat_mode == 0:
            return 'chat mode is 0, no talking'
        session = Session()
        all_pic_info = session.query(PicInfo.pic_name, PicInfo.pic_link, PicInfo.group_id).filter(PicInfo.pic_name != 'pic_name_list').all()
        session.close()
        # --------- 這邊有效能問題需要解決 ---------
        # 目前是每一句對話都去抓全部的 DB 回來，然後丟進 for loop 掃描全部的內容
        # 1. DB server 的運算部分目前已知要錢，所以不要讓它算，要靠 Cloud Function 那邊的資源
        # 2. 所以整個抓回來再算是一種方法，但需要思考能不能不要每次都跟 DB 拿，而是哪邊有 server cache 之類的
        match_list = []
        # 收到的格式為:  [('尷尬又不失禮貌的微笑', 'https://i.imgur.com/XTNxbnr.jpg', 'C62f513a68fb81e84aa84a7c3c5f503d6')]
        # 並可用 .pic_name  .pic_link  .group_id 的方式獲取
        for pic in all_pic_info:
            # 這邊在解決如果 test 與 test2 同時存在，那 test2 將永遠不會被匹配到的問題，預期要取匹配到字數最長的
            match = re.search(str(pic.pic_name), self.chat.event.message.text, re.IGNORECASE)
            if match and self.chat.chat_mode == 1 and len(pic.pic_name) >= self.chat.trigger_chat:
                match_list.append(pic)
            elif match and self.chat.chat_mode == 2 and self.chat.group_id == pic.group_id and len(pic.pic_name) >= self.chat.trigger_chat:
                match_list.append(pic)
        if match_list:
            # pic_name_list = [ pic.pic_name for pic in match_list ]
            # key 這邊解決了如果 match 多組 pic_name，會依照 pic_name 長度排序
            match_list.sort(key=lambda x: len(x.pic_name))
            # 排序後取 match 字數最多的也就是最右邊的
            matched_pic_name = match_list[-1].pic_name
            # 可能 pic_name_list 裡面其實有多組與 matched_pic_name 一樣的，全留下後面拿來 random
            match_list_with_matched_pic_name = [ pic for pic in match_list if pic.pic_name == matched_pic_name ]
            # 若 chat_mode = 1，group_id 會設定為 None 則邏輯會走到這裡，select 的時候就不能把
            from random import Random
            random_index = Random().choice(range(len(proper_pic_name_list)))
            self.reply_content = match_list_with_matched_pic_name[random_index].pic_link
            self.__reply_msg(
                self.chat.event.reply_token,
                self.reply_content,
                content_type='image')
        else:
            pass

    def get_reply_content(self):
        '''
        測試用
        '''
        print(self.reply_content)



if __name__ == '__main__':
    pass
