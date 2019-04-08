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
CONNECTION_NAME = getenv("INSTANCE_CONNECTION_NAME",
                         "<YOUR INSTANCE CONNECTION NAME>")
DB_USER = getenv("MYSQL_USER", "<YOUR DB USER>")
DB_PASSWORD = getenv("MYSQL_PASSWORD", "<YOUR DB PASSWORD>")
DB_NAME = getenv("MYSQL_DATABASE", "<YOUR DB NAME>")
USER_INFO_CONNECT = ("mysql+pymysql://root:" + DB_PASSWORD + "@/" +
                     DB_NAME + "?unix_socket=/cloudsql/" + CONNECTION_NAME)

# 設定圖片名稱的字數的長度在此控制
PIC_NAME_LOW_LIMIT = 2
PIC_NAME_HIGH_LIMIT = 15
