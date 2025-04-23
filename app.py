from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = '4dS0OX7GWaQ0vxWXuyLvU/XE7j7chKo1wvfAkL7DtyNAqXw8ftLTPfvLslveL400W7dl1h6X8Bbylmw1eOTCluerae4ozctT1YrjdfYNg54Cz+xudN73djDFh9I5NneHcqkxrgZ5AkHyOteqQCoRqQdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = '90b66812b12a2ca40a2508d288b52273'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    print("📩 Body:", body)
    print("🔑 Signature from LINE:", signature)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ Invalid signature.")
        abort(403)

    return "OK"

queue = []

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    msg = event.message.text.strip().lower()

    if msg == "book":
        if user_id not in queue:
            queue.append(user_id)
            reply = f"✅ คุณได้ทำการจองคิวเรียบร้อยแล้ว 🎉\nคุณอยู่ในลำดับที่ {len(queue)}"
        else:
            reply = f"📌 คุณจองคิวไว้แล้ว\nลำดับของคุณคือ {queue.index(user_id) + 1}"

    elif msg == "cancel":
        if user_id in queue:
            queue.remove(user_id)
            reply = "❌ คุณได้ยกเลิกคิวเรียบร้อยแล้วครับ"
        else:
            reply = "❗️คุณยังไม่มีคิวที่จองไว้"

    elif msg == "queue":
        if queue:
            reply_lines = [f"{i+1}. {'คุณ' if uid == user_id else 'ผู้ใช้'}" for i, uid in enumerate(queue)]
            reply = "📋 รายชื่อคิวทั้งหมด:\n" + "\n".join(reply_lines)
        else:
            reply = "📭 ขณะนี้ยังไม่มีคิวใด ๆ เลย"

    else:
        reply = "กรุณาพิมพ์ 'book' เพื่อจองคิว 🙏\nหรือ 'queue' เพื่อดูคิว\nหรือ 'cancel' เพื่อยกเลิกคิว"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5050)