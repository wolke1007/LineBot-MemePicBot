from os import getenv

# imgur key
CLIENT_ID = getenv("CLIENT_ID")
CLIENT_SECRET = getenv("CLIENT_SECRET")
ALBUM_ID = getenv("ALBUM_ID")
ACCESS_TOKEN = getenv("ACCESS_TOKEN")
REFRESH_TOKEN = getenv("REFRESH_TOKEN")

# line bot key
LINE_CHANNEL_ACCESS_TOKEN = getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = getenv("LINE_CHANNEL_SECRET")

# MySQL 連線資訊
DB_DOMAIN = getenv("DB_DOMAIN", "<YOUR DB SEVER DOMAIN NAME>")
DB_NAME = getenv("DB_NAME", "<YOUR DB NAME>")
DB_USER = getenv("DB_USER", "<YOUR DB USER>")
DB_PASSWORD = getenv("DB_PASSWORD", "<YOUR DB PASSWORD>")
DB_PORT = getenv("DB_PORT", "<YOUR DB SEVER PORT>")
CONNECTION_INFO = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_DOMAIN}:{DB_PORT}/{DB_NAME}"

# 設定圖片名稱的字數的長度在此控制
PIC_NAME_LOW_LIMIT = 2
PIC_NAME_HIGH_LIMIT = 15

HELP_CONTENT = ("貼心提醒您，請勿洩漏個資\n"
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

if __name__ == '__main__':
    pass
