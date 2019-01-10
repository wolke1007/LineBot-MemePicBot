# -*- coding: utf-8 -*-
from pandas import DataFrame
from numpy import array
from matplotlib.pyplot import subplots
from io import BytesIO
from six import iteritems
from PIL import Image
from matplotlib.font_manager import FontProperties
import os
from db_manipulate import DBManipulate as dbm


class PicNameList():
    @staticmethod
    def _render_mpl_table(data, col_width=3.0, row_height=0.625, font_size=12,
                          header_color='#40466e', row_colors=['#f1f1f2', 'w'],
                          edge_color='w', bbox=[0, 0, 1, 1], header_columns=0,
                          ax=None, **kwargs):
        print('enter render_mpl_table')
        if ax is None:
            size = (array(data.shape[::-1]) + array([0, 1])) * \
                    array([col_width, row_height])
            fig, ax = subplots(figsize=size)
            ax.axis('off')
        # 取當前 main.py 的檔案位置，因為我上傳的字型檔跟它放一起
        dir_path = os.path.dirname(os.path.realpath(__file__))
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

    @staticmethod
    def _turn_table_into_pic(table_object):
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

    @staticmethod
    def get_binary_pic(res):
        # res 格式為:  [('1',), ('ABC',)]
        res = [_[0] for _ in res]
        # 利用 set 將重複的字串給刪去
        res = list(set(res))
        # 圖片中的 columns 數
        columns_cnt = 6
        # 取餘數用 None 補滿，讓每個 column 都有內如，pd.DataFrame 才不會變成只有一行
        res.extend([None for i in range(len(res) % columns_cnt)])
        # 將 list 包成 [[1,2,3], [1,2,3]] 這樣的格式再餵給 pd.DataFrame
        # (注意，裡面每個 list 一定要數量一致)
        res = [res[i:i + columns_cnt] for i in range(0, len(res), columns_cnt)]
        print('debug res[-1]:', res[-1])
        pd_res = DataFrame(res)
        table_object = PicNameList._render_mpl_table(pd_res, header_columns=0,
                                                     col_width=2.0)
        table_object = table_object.get_figure()
        binary_pic = PicNameList._turn_table_into_pic(table_object)
        return binary_pic


class HelpText():
    @staticmethod
    def get_help_content():
        help_content = (
            "貼心提醒您請勿洩漏個資\n"
            "嚴 禁 上 傳 色 情 圖 片\n"
            "(作者: 我不想被 Imgur banned 拜託配合了ＱＡＱ\n"
            "使用教學：\n"
            "step 1. 設定圖片名稱，例如 #我是帥哥#\n"
            "step 2. 上傳圖片，系統會回傳上傳成功\n"
            "step 3. 聊天時提到設定的圖片名稱便會觸發貼圖\n"
            "\n"
            "設定教學：\n"
            "--mode chat_mode 0~2\n"
            "0 = 不回圖\n"
            "1 = 隨機回所有群組創的圖(預設)\n"
            "2 = 只回該群組上傳的圖\n"
            "\n"
            "--mode trigger_chat 2~15\n"
            "設定在此群組裡超過幾字才回話，可以設為 2~15 \n"
            "\n"
            "備註:\n"
            "1. 圖片字數有限制，空白或是特殊符號皆算數\n"
            "2. 設定同圖片名稱則會蓋掉前面上傳的\n"
            "3. 若上傳URL則必須為 http 開頭 .jpg .gif .png 結尾\n"
            "(目前尚未實作完成)\n"
            "4. 建議在 Line 設定將「自動下載照片」取消打勾\n"
            "設定 > 照片。影片 > 自動下載照片\n"
            "5. 如果設定多次名字再上傳圖片，則是多個關鍵字對應同一張圖片\n"
            "6. --list 可以讓 BOT 回你現有圖片名稱的表格\n"
        )  # line 手機版莫約 15 個中文字寬度就會換行
        return help_content


class Mode():
    @staticmethod
    def set_trigger_chat(msg_content, group_id):
        print('msg_content == "--mode"')  # debug
        # --mode trigger_chat 1
        try:
            mode = int(msg_content[-2:].strip(' '))
        except ValueError:
            reply_content = ("trigger_chat 後需設定介於 2~15 的數字"
                             "，如 --mode trigger_chat 15")
            params_dict, pre_sql = None
            return params_dict, pre_sql, reply_content
        # 不允許使用者設置低於 2 或是大於 15 個字元
        if mode < PIC_NAME_LOW_LIMIT or mode > PIC_NAME_HIGH_LIMIT:
            reply_content = ("trigger_chat 後需設定介於 2~15 的數字，"
                             "如 --mode trigger_chat 15")
            params_dict, pre_sql = None
            return params_dict, pre_sql, reply_content
        params_dict = {
            'group_id': group_id,
            'trigger_chat': mode
        }
        update_pre_sql = ("UPDATE system SET trigger_chat=:trigger_chat "
                          "WHERE group_id=:group_id")
        reply_content = '更改 trigger_chat 為 ' + str(mode)
        return params_dict, update_pre_sql, reply_content

    @staticmethod
    def set_chat_mode(msg_content, group_id):
        try:
            mode = int(msg_content[-1])
        except ValueError:
            reply_content = ("chat_mode 後需設定介於 0~2 的數字，"
                             "如 --mode chat_mode 2")
            params_dict, pre_sql = None
            return params_dict, pre_sql, reply_content
        params_dict = {
            'group_id': group_id,
            'chat_mode': mode
        }
        update_pre_sql = ("UPDATE system SET chat_mode=:chat_mode "
                          "WHERE group_id=:group_id")
        reply_content = '更改 chat_mode 為 ' + str(mode)
        return params_dict, update_pre_sql, reply_content

    @staticmethod
    def get_mode_status(system_config, group_id):
        if system_config:
            group_id_list = [i[0] for i in system_config]
            index = group_id_list.index(group_id)
    # system_config[index] 會回傳一個 tuple 類似像 ('Cxxxxxx', 1, 1, 3)
    # 從左至右分別對應: group_id,	chat_mode, retrieve_pic_mode, trigger_chat
    #                        其中 chat_mode 的設定：0 = 不回圖
    #                                             1 = 隨機回所有 group 創的圖(預設)
    #                                             2 = 只回該 group 上傳的圖
    #                        其中 trigger_chat 預設為 3 個以上的字才回話，可以設為 2~15
            system_config = system_config[index]
            reply_content = ("[當前模式為] "
                             "chat_mode:" +
                             str(system_config[1]) + " ,"
                             "retrieve_pic_mode:" +
                             str(system_config[2]) + " ,"
                             "trigger_chat:" +
                             str(system_config[3])
                             )
            return reply_content
        else:
            reply_content = "尚無 mode 資料，請再試一次"
            return reply_content


class DeletePic():
    @staticmethod
    # 基本上不在 extension.py 中做 DB 的操作
    # 但這個刪除圖片的部分例外
    def del_pic(pic_name, group_id):
        print('enter del_pic')  # debug
        group_id = None if group_id == 'NULL' else group_id
        if group_id is None:
            print('group_id is NULL')
            params_dict = {
            'pic_name': pic_name
            }
            update_pre_sql = ("DELETE FROM pic_info "
                              "WHERE pic_name=:pic_name "
                              "AND group_id=NULL")
            db_res = dbm.delete_from_db(update_pre_sql, params_dict)
            reply_content = "刪除非群組圖片名稱成功" if db_res else "刪除失敗"
            return reply_content
        else:
            print('group_id is exist')
            params_dict = {
            'pic_name': pic_name,
            'group_id': group_id
            }
            update_pre_sql = ("DELETE FROM pic_info "
                              "WHERE pic_name=:pic_name "
                              "AND group_id=:group_id")
            db_res = dbm.delete_from_db(update_pre_sql, params_dict)
            reply_content = "刪除群組內的圖片名稱成功" if db_res else "刪除失敗"
            return reply_content


if __name__ == '__main__':
    pass
