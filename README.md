Google Cloud Function

Meme Pic Line Bot (BETA v1.1.0)

目前功能:
1. 回圖功能
    - 設定圖片名稱
    - 上傳貼圖
    - 掃描對話，並回應對話中有出現圖片名稱的圖
    - 封鎖使用者機制
    - 設定多個關鍵字，對應一張圖片

已知 Bug:
1. 目前有潛在的效能問題，因為每句對話都會去撈所有 pic_name column，需要實作 cache 機制去
   固定時間將內容撈進 memory 來減輕 DB server 負擔


已修復 Bug:
1. 名字前面重複的話會永遠用較短的名字做回應
e.g. 如 test or test2 兩張圖，test2 將永遠不會出現因為先 match test 就直接回應了
2. 


待實作 Feature:
1. 完善 debug mode
2. meme pic 製作功能，效果預期跟 meme gen 一樣，有 open source code 可以參考 
3. 貼 URL 也可以上傳的功能
4. 刪除圖片或刪除關鍵字
5. System Table 用以控制回話等等的功能
6. 讓 user report 不好的圖片機制
    - 預計是讓使用者貼上哪句話出現不好的圖片，甚至可以附註為什麼，不加附註者即完全讓管理員決定是否刪除
    - 接著去掃描可能是哪些關鍵字的圖片有問題然後列出來，管理員只要人工直接檢查圖片即可