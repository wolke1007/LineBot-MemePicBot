# Meme Pic Line Bot (BETA v3.1.5) 
此 Line Bot 設計宗旨為增進聊天樂趣用

若想試玩此 BOT 請搜尋 Line ID "@srh5401g"
或掃描以下 QR Code 加入好友
![Alt text](intro_data/QRcode.png "QR Code")

# 功能
1. 機器人根據聊天中的關鍵字回覆已設定的圖片給該聊天群組
2. 讓使用者上傳關鍵字與圖片組合
3. 列出目前已設定過的關鍵字
4. 刪除已設定過的關鍵字
5. 設定機器人在該聊天群組的回圖行為
    1.不回圖
    2.隨機回所有群組創的圖(預設)
    3.只回該群組上傳的圖
6. 設定機器人在該聊天群組裡關鍵字符合超過(大於等於)幾字才回話，可以設為 2~15
e.g. trigger_chat = 3
"帥哥" -> 不會被觸發
"我是帥哥" -> 會被觸發

# 使用教學
## 一般使用
##### 1. 設定圖片名稱，例如 #我是帥哥# (註1 2 3)
![Alt text](intro_data/set_keyword.png "Set Keyword")
    1-1. 圖片字數有限制，空白或是特殊符號皆算數
    1-2. 設定同圖片名稱則會蓋掉前面上傳的
    1-3. 如果設定多次名字再上傳圖片，則是多個關鍵字對應同一張圖片
##### 2. 上傳圖片或是貼上圖片的 URL，系統會回傳上傳成功 (註4)

    2-1. 若上傳URL則必須為 http 開頭(https亦可) .jpg .gif .png 結尾（其餘副檔名不支援)
##### 3. 聊天時提到設定的圖片名稱便會觸發貼圖

## 聊天室設定
#### 設定機器人在該聊天群組的回圖行為
##### `--mode chat_mode 0~2` 
* 0 = 不回圖
* 1 = 隨機回所有群組創的圖(預設)
* 2 = 只回該群組上傳的圖

#### 設定機器人在該聊天群組裡關鍵字符合超過(大於等於)幾字才回話
##### `--mode trigger_chat 2~15`
```
e.g. trigger_chat = 3
     "帥哥" -> 不會被觸發
     "我是帥哥" -> 會被觸發
```
## 其他功能
#### 列出目前已設定過的關鍵字
##### `--list` 

#### 刪除已設定過的關鍵字
##### `--delete <圖片名稱>` 
```
e.g. --delete 我是帥哥
```

# Bug

## 已知問題(或淺在問題)
1. 目前有潛在的效能問題，因為每句對話都會去撈所有 pic_name column

## 已修復 Bug
1. 名字前面重複的話會永遠用較短的名字做回應
```
e.g. 如 test or test2 兩張圖，test2 將永遠不會出現因為先 match test 就直接回應了
```


## 待實作 Feature
* meme pic 製作功能，效果預期跟 meme gen 一樣，有 open source code 可以參考
  * 功能詳見 https://memegen.link/
  * source code https://github.com/jacebrowning/memegen
* 讓 user report 不好的圖片機制
  * 預計是讓使用者回報哪句話出現不好的圖片，甚至可以附註為什麼
  * 管理員能夠透過對話獲得回報的內容並人工檢查圖片並刪除
* 管理員功能
    * 管理員登入/登出功能(可以研究能不能用 3rd 的 auth 機制之類的)
    * banned 帳號
    * 檢視使用者舉報有問題的內容
    * 使用最高權限直接刪除圖片

## 備註
1. 圖片字數有限制，空白或是特殊符號皆算數
2. 設定同圖片名稱則會蓋掉前面上傳的
3. 如果設定多次名字再上傳圖片，則是多個關鍵字對應同一張圖片
4. 若上傳URL則必須為 http 開頭(https亦可) .jpg .gif .png 結尾（其餘副檔名不支援)
5. 建議在 Line 設定將「自動下載照片」取消打勾
   設定 > 照片。影片 > 自動下載照片