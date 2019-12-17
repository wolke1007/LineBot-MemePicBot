# -*- coding: utf-8 -*-
from config import *
from config_for_test import *  # debug
from pandas import DataFrame
from numpy import array
from matplotlib.pyplot import subplots
from io import BytesIO
from six import iteritems
from PIL import Image
from matplotlib.font_manager import FontProperties
from linebot import LineBotApi
from linebot.models import TextSendMessage
from ..ORM import PicInfo, System, UserInfo, Session
from .imgur import Imgur
import re
from os import path


line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)


class Skill(Imgur):

    def _reply_msg(self, content_type, function_name=None):
        '''
        1. 使用者主動敲 Bot，Bot 回覆人叫做 reply
        2. 這種需要 reply_token 才知道要回誰，
           且 reply_token 過一小段時間後會自動過期(或許是幾秒鐘後，沒文件明說)
           所以機器人不能太晚回話
        3. 可回文字 or 圖片
        '''
        if self.debug:
            if self.echo:
                print(f'function name:{function_name}, self.reply_content: {self.reply_content}')
            return self.reply_content
        else:
            if content_type is 'text':
                line_bot_api.reply_message(
                    self.chat.event.reply_token,
                    TextSendMessage(text=self.reply_content))
            elif content_type is 'image':
                line_bot_api.reply_message(
                    self.chat.event.reply_token,
                    ImageSendMessage(preview_image_url=self.reply_content,
                                    original_content_url=self.reply_content))

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

        dir_path = path.dirname(path.realpath('STHeitiMedium.ttc'))
        print(dir_path)
        # STHeitiMedium.ttc 是中文字型檔，有了它 matplotlib 才有辦法印出中文，我擔心 GCP 沒有內建就自己上傳了
        font = FontProperties(fname=dir_path + "/STHeitiMedium.ttc", size=14)
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
        # 利用 set 將重複的字串給刪去
        res = list(set(res))
        # 字數從小到大排
        res.sort(key=lambda x: len(x))
        columns_cnt = 6
        # 取餘數用 None 補滿，讓每個 column 都有內容，pd.DataFrame 才不會變成只有一行
        res.extend([None for i in range(len(res) % columns_cnt)])
        # 將 list 包成 [[1,2,3], [1,2,3]] 這樣的格式再餵給 pd.DataFrame
        # (注意，裡面每個 list 一定要數量一致)
        res = [ res[i:i + columns_cnt] for i in range(0, len(res), columns_cnt) ]
        pd_res = DataFrame(res)
        table_object = self.__render_mpl_table(pd_res, header_columns=0,
                                                       col_width=2.0)
        table_object = table_object.get_figure()
        binary_pic = self.__turn_table_into_pic(table_object)
        return binary_pic

    def get_help(self):
        if self.chat.event.message.text == '--help' or self.chat.event.message.text == '-h':
            self.reply_content = HELP_CONTENT
            self._reply_msg(
                    content_type='text',
                    function_name=self.get_help.__name__)
        else:
            pass

    def delete_pic(self):
        '''
        目前僅讓使用者刪除該聊天室且為自己創的圖片
        '''
        #TODO 這邊改用 ORM 直接進行 delete 操作
        if self.chat.event.message.text[:9] == '--delete ':
            pic_name = self.chat.event.message.text[9:]
            session = Session()
            
            delete_success = session.query(PicInfo).filter(PicInfo.pic_name == pic_name)\
                                    .filter(PicInfo.user_id == self.chat.event.source.user_id)\
                                    .filter(PicInfo.group_id == self.chat.group_id)\
                                    .delete()
            session.commit()
            session.close()
            if delete_success:
                self.reply_content = f'{pic_name} 已刪除'
            else:
                self.reply_content = f'圖片未刪除\n(提醒: 不能刪除別人的圖片，也不能刪除其他聊天室的圖片)'
            self._reply_msg(
                content_type='text',
                function_name=self.delete_pic.__name__)
        else:
            pass

    def reply_pic_name_list(self):
        if self.chat.event.message.text == '--list':
            session = Session()
            # 撈出除了 pic_name_list 這張圖片以外的所有圖片名稱後做成表
            all_pic_info = session.query(PicInfo.pic_name, PicInfo.pic_link, PicInfo.group_id).filter(PicInfo.pic_name != '--pic_name_list').all()
            session.query(PicInfo.pic_link).filter(PicInfo.pic_name == '--pic_name_list').update({PicInfo.pic_link: 'NULL', PicInfo.group_id: self.chat.group_id})
            session.commit()
            session.close()
            all_pic_name_in_db = [ pic.pic_name for pic in all_pic_info ]
            self.chat.binary_pic = self.__get_binary_pic(all_pic_name_in_db)
            self.chat.is_image_event = True
            pic_link = self.upload_to_imgur_with_image()
            if self.reply_content == '上傳成功':
                # 複寫名字為 'pic_name_list' 的 pic_link
                print('上傳成功')
                session = Session()
                session.query(PicInfo.pic_link).filter(PicInfo.pic_name == 'pic_name_list').update({PicInfo.pic_link: pic_link})
                session.commit()
                session.close()
                self.reply_content = pic_link
                self._reply_msg(
                    content_type='image',
                    function_name=self.reply_pic_name_list.__name__)
            else:
                print('上傳失敗')
                self._reply_msg(
                    content_type='text',
                    function_name=self.reply_pic_name_list.__name__)
        else:
            pass

    def set_pic_name(self):
        '''
        1. 不允許使用者於同個聊天群組新增同個關鍵字不同圖片
           若命名為已用過關鍵字，則新圖片覆蓋舊圖片
        2. 皆以小寫儲存圖片名字，增加未來比對命中率
        3. 禁止使用者使用 '--' 開頭的字串當作命名避免系統用關鍵字被命名
        '''
        if self.chat.event.message.text[0] == '#' and self.chat.event.message.text[-1] == '#':
            pic_name = self.chat.event.message.text[1:-1]
            print(pic_name)
            # if pic_name[:2] == '--':
            #     self.reply_content = '-- 開頭的名字為系統保留禁止使用'
            #     self._reply_msg(
            #         content_type='text',
            #         function_name=self.set_pic_name.__name__)
            #     return 'forbid user to use name with -- prefix'
            session = Session()
            had_named_pic_with_NULL_link = session.query(PicInfo)\
                .filter(PicInfo.user_id == self.chat.event.source.user_id)\
                .filter(PicInfo.group_id == self.chat.group_id)\
                .filter(PicInfo.pic_link == 'NULL').all()
            if had_named_pic_with_NULL_link:
                session.query(PicInfo.pic_link)\
                    .filter(PicInfo.user_id == self.chat.event.source.user_id)\
                    .filter(PicInfo.pic_link == 'NULL')\
                    .update({PicInfo.pic_name: pic_name})
                self.reply_content = f'圖片名稱已更新: {pic_name}，請上傳圖片或圖片連結'
                session.commit()
            else:
                had_pic_with_this_name = session.query(PicInfo)\
                    .filter(PicInfo.user_id == self.chat.event.source.user_id)\
                    .filter(PicInfo.group_id == self.chat.group_id)\
                    .filter(PicInfo.pic_name == pic_name).all()
                if had_pic_with_this_name:
                    session.query(PicInfo.pic_link)\
                        .filter(PicInfo.user_id == self.chat.event.source.user_id)\
                        .filter(PicInfo.group_id == self.chat.group_id)\
                        .filter(PicInfo.pic_name == pic_name)\
                        .update({PicInfo.pic_link: 'NULL'})
                    self.reply_content = f'{pic_name} 的舊圖片連結已清除，請重新上傳圖片或圖片連結'
                    session.commit()
                else:
                    picinfo_to_add = PicInfo(user_id=self.chat.event.source.user_id,\
                                             pic_name=pic_name,\
                                             pic_link='NULL',\
                                             group_id=self.chat.event.source.group_id)
                    session.add(picinfo_to_add)
                    self.reply_content = f'圖片名稱已設定: {pic_name}，請上傳圖片或圖片連結'
                    session.commit()
            session.close()
            self._reply_msg(
                content_type='text',
                function_name=self.set_pic_name.__name__)
        else:
            pass

    def send_pic_back(self):
        if self.chat.chat_mode == 0:
            return 'chat mode is 0, no talking'
        if (self.chat.event.message.text[0] == '#' and self.chat.event.message.text[-1] == '#') or \
            self.chat.event.message.text[:2] == '--':
            return 'this chat could be a command, no need to send pic'
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
            print('match_list: ', match_list)
            # pic_name_list = [ pic.pic_name for pic in match_list ]
            # key 這邊解決了如果 match 多組 pic_name，會依照 pic_name 長度排序
            match_list.sort(key=lambda x: len(x.pic_name))
            # 排序後取 match 字數最多的也就是最右邊的
            matched_pic_name = match_list[-1].pic_name
            # 可能 pic_name_list 裡面其實有多組與 matched_pic_name 一樣的，全留下後面拿來 random
            match_list_with_matched_pic_name = [ pic for pic in match_list if pic.pic_name == matched_pic_name ]
            from random import Random
            random_index = Random().choice(range(len(match_list_with_matched_pic_name)))
            self.reply_content = match_list_with_matched_pic_name[random_index].pic_link
            self._reply_msg(
                content_type='image',
                function_name=self.send_pic_back.__name__)
        else:
            pass

    def test_func(self):
        if self.debug:
            if self.echo:
                # print(self.reply_content)
                return self.reply_content
            return self.reply_content

if __name__ == '__main__':
    pass
