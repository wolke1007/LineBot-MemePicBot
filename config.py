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


if __name__ == '__main__':
    pass
