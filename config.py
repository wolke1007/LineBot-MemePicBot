from os import getenv
from os import getenv

# imgur key
CLIENT_ID = "ef420e58e8af248"
CLIENT_SECRET = "1e0b2834e232b9ca67ccb3d6b2076d7160614e10"
IMAGE_URL = 'http://www.personal.psu.edu/afr3/blogs/siowfa12/success.jpeg'
ALBUM_ID = 'UxgXZbe'
ACCESS_TOKEN = 'f7256765b702f940b6f9124bd6a6d53b8d7b9c67'
REFRESH_TOKEN = 'b9058ff301a411c2dcbef44ae5b5c6ca237d06c0'

# line bot key
LINE_CHANNEL_ACCESS_TOKEN = 'FxI3Qlfn3Mwyne/OujcIsYfOQCcIOZTUIYbDF2d41/GZAlQv2p5FGkp/ategG6xe0ErAsJCQOeHxdSM1xJ7uCejar1IGM5tDCzSFp40QmWs0BEjVec2nkacPIrL8Hh8XVvBxUgEUsGG6U+nvyGRClgdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = '7c2930cb70180aae136f76504fba88bd'

# MySQL 連線資訊
CONNECTION_NAME = getenv(
  'INSTANCE_CONNECTION_NAME',
  '<YOUR INSTANCE CONNECTION NAME>')
DB_USER = getenv('MYSQL_USER', '<YOUR DB USER>')
DB_PASSWORD = getenv('MYSQL_PASSWORD', '<YOUR DB PASSWORD>')
DB_NAME = getenv('MYSQL_DATABASE', '<YOUR DB NAME>')
USER_INFO_CONNECT = 'mysql+pymysql://root:'+DB_PASSWORD+'@/'+DB_NAME+'?unix_socket=/cloudsql/'+CONNECTION_NAME

# 設定圖片名稱的字數的長度在此控制
PIC_NAME_LOW_LIMIT = 2
PIC_NAME_HIGH_LIMIT = 15