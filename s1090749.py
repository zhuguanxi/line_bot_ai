
from flask import Flask, request, abort, jsonify
import google.generativeai as genai
# 載入 json 標準函式庫，處理回傳的資料格式
import json
import sqlite3
# 載入 LINE Message API 相關函式庫
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FlexSendMessage, LocationSendMessage,
    VideoSendMessage, ImageSendMessage,StickerSendMessage,
)

app = Flask(__name__)

access_token = 'otjZNXRFaXgWz57E5WaP+cbosZm9HA0LGY5fu7AhzCcl2/wzDlxFOHAO6k5i/F/zTnFED9P09LjvsPS3z+40n/orPWgQcMWv0Sn7LuRgEJeEBY8ZyNNDrICLc7bYWoVnCxgybVYTu/q/LwV8VaXxpwdB04t89/1O/w1cDnyilFU='
secret = '311180194e126fd06a7ebd0e6eb3189f'
line_bot_api = LineBotApi(access_token)              # 確認 token 是否正確
handler = WebhookHandler(secret) 

@app.route("/")
def hello():
    return "Line Webhook is activel!"

@app.route("/callback",methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: "+body)

    try:
        handler.handle(body,signature)
    except InvalidSignatureError:
        print ("Invalid signature")
        abort(400)

    return 'OK'

@app.route('/history/<user_id>', methods=['GET'])
def get_history(user_id):
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT message, timestamp FROM messages WHERE user_id=? ORDER BY timestamp", (user_id,))
        rows = cursor.fetchall()
    return json.dumps([{"message": r[0], "timestamp": r[1]} for r in rows], ensure_ascii=False)

@app.route('/history/<user_id>', methods=['DELETE'])
def delete_history(user_id):
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE user_id=?", (user_id,))
        conn.commit()
    return jsonify({"status": "success", "message": f"Deleted messages for user {user_id}."})


@handler.add(MessageEvent,message=TextMessage)
def handle_message(event):
    print(f"使用者 ID：{event.source.user_id}")
    user_id = event.source.user_id  # 加這行取得使用者 ID
    message = event.message.text
    save_message(user_id, "USER: " + message)  # 儲存訊息進資料庫

    message = event.message.text
    if message == 'sticker':
        output = StickerSendMessage(
            package_id='6362',
            sticker_id='11087923'
        )
    elif message == 'image':
        output = ImageSendMessage(
            original_content_url = "https://ithelp.ithome.com.tw/upload/images/20220925/20151681EaMkK6ROvq.jpg",
            preview_image_url = "https://ithelp.ithome.com.tw/upload/images/20220925/20151681EaMkK6ROvq.jpg"
        )

    elif message == 'video':
        print("video 被觸發")
        output = VideoSendMessage(
            original_content_url="https://media.w3.org/2010/05/sintel/trailer.mp4",
            preview_image_url="https://upload.wikimedia.org/wikipedia/commons/9/9a/Gull_portrait_ca_usa.jpg"
        )

    elif message == 'location':
        output = LocationSendMessage(
            title='Mask Map',
            address='YZU',
            latitude=24.970130,
            longitude=121.263303
        )
    elif message == "學deep learning要從哪邊開始":
        try:
            genai.configure(api_key="AIzaSyBZ2Rqkk4bjW1ZQHKAbH_dwmEN5VvUqHXI")
            model = genai.GenerativeModel("gemini-1.5-flash")
            chat = model.start_chat()
            reply = chat.send_message("學deep learning要從哪邊開始")
            output = TextSendMessage(text=reply.text)
        except Exception as e:
            output = TextSendMessage(text="發生錯誤，請稍後再試～")
    else:
        output = TextSendMessage(text=message)
        
    save_message(user_id, "BOT: " + output.text)
    line_bot_api.reply_message(
        event.reply_token,
        output)
    
def init_db():
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

init_db()
def save_message(user_id, message):
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (user_id, message) VALUES (?, ?)", (user_id, message))
        conn.commit()


if __name__ == "__main__":
    app.run()
