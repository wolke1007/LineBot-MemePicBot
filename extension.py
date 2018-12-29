# -*- coding: utf-8 -*-
from pandas import DataFrame
from numpy import array
from matplotlib.pyplot import subplots
from io import BytesIO
from six import iteritems
from PIL import Image
from matplotlib.font_manager import FontProperties


class PicNameList():
    @staticmethod
    def render_mpl_table(data, col_width=3.0, row_height=0.625, font_size=12,
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
    def turn_table_into_pic(table_object):
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
    def get_binary_pic():
        # 撈出除了 pic_name_list 這張圖片以外的所有圖片名稱
        select_pre_sql = ("SELECT pic_name FROM pic_info "
                          "WHERE pic_name != 'pic_name_list'")
        res = dbm.select_from_db(select_pre_sql, params_dict={})
        # res 格式為:  [('1',), ('ABC',)]
        res = [_[0] for _ in res]
        # 利用 set 將重複的字串給刪去
        res = list(set(res))
        # 圖片中的 columns 數
        columns_cnt = 6
        # 取餘數用 None 補滿，讓每個 column 都有內如，pd.DataFrame 才不會變成只有一行
        res.extend([None for i in range(len(res) % columns_cnt)])
        # 將 list 包成 [[1,2,3], [1,2,3]] 這樣的格式再餵給 pd.DataFrame
        # (注意，裡面每個 list 一定要數量一致喔)
        res = [res[i:i + columns_cnt] for i in range(0, len(res), columns_cnt)]
        print('debug res[-1]:', res[-1])
        pd_res = DataFrame(res)
        table_object = self.render_mpl_table(pd_res, header_columns=0,
                                             col_width=2.0)
        table_object = table_object.get_figure()
        binary_pic = self.turn_table_into_pic(table_object)


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


if __name__ == '__main__':
    pass
