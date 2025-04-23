import json
from datetime import datetime
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = '4dS0OX7GWaQ0vxWXuyLvU/XE7j7chKo1wvfAkL7DtyNAqXw8ftLTPfvLslveL400W7dl1h6X8Bbylmw1eOTCluerae4ozctT1YrjdfYNg54Cz+xudN73djDFh9I5NneHcqkxrgZ5AkHyOteqQCoRqQdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = '90b66812b12a2ca40a2508d288b52273'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

queue_file = "queue.json"
queue = []
queue_date = datetime.now().date()

# === Persistence ===
def save_queue():
    data = {
        "queue": queue,
        "date": str(queue_date)
    }
    with open(queue_file, "w") as f:
        json.dump(data, f)

def load_queue():
    global queue, queue_date
    try:
        with open(queue_file, "r") as f:
            data = json.load(f)
            queue = data.get("queue", [])
            queue_date = datetime.strptime(data.get("date"), "%Y-%m-%d").date()
    except:
        queue = []
        queue_date = datetime.now().date()

def check_reset_queue():
    global queue, queue_date
    today = datetime.now().date()
    if today != queue_date:
        queue = []
        queue_date = today
        save_queue()

load_queue()

# === LINE Webhook ===
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(403)
    return "OK"

# === Message Handler ===
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    check_reset_queue()

    user_id = event.source.user_id
    msg = event.message.text.strip().lower()
    reply = ""

    if msg == "book":
        if any(entry["user_id"] == user_id for entry in queue):
            position = next(i for i, entry in enumerate(queue) if entry["user_id"] == user_id)
            reply = f"📌 You have already booked.\nYour queue position is {position + 1}."
        else:
            timestamp = datetime.now().isoformat()
            queue.append({"user_id": user_id, "time": timestamp})
            save_queue()
            reply = f"✅ Booking successful! 🎉\nYour queue number is {len(queue)}."

    elif msg == "cancel":
        for i, entry in enumerate(queue):
            if entry["user_id"] == user_id:
                queue.pop(i)
                save_queue()
                reply = "❌ Your booking has been canceled."
                break
        else:
            reply = "⚠️ You don't have a booking to cancel."

    elif msg == "queue":
        if queue:
            reply_lines = [
                f"{i+1}. {'You' if entry['user_id'] == user_id else 'User'} at {entry['time'][11:16]}"
                for i, entry in enumerate(queue)
            ]
            reply = "📋 Current Queue:\n" + "\n".join(reply_lines)
        else:
            reply = "📭 No one is in the queue at the moment."

    else:
        reply = (
            "Please type 'book' to reserve a queue slot 🙏\n"
            "Type 'queue' to view the current queue\n"
            "Type 'cancel' to cancel your booking"
        )

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5050)