import json
from datetime import datetime, timedelta, timezone
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
            entry = next(entry for entry in queue if entry["user_id"] == user_id)
            position = next(i for i, e in enumerate(queue) if e["user_id"] == user_id)
            queues_left = position
            reply = (
                "✨ *Booking Already Exists* ✨\n"
                "-----------------------------\n"
                f"🎟️ *Queue Number*: `{entry['number']}`\n"
                f"🕒 *Time*: `{datetime.fromisoformat(entry['time']).strftime('%H:%M')}`\n"
                f"📊 *Position in Queue*: `{queues_left}`\n"
                "-----------------------------"
            )
        else:
            timestamp = datetime.now(timezone(timedelta(hours=7))).isoformat()
            last_number = (
                max([int(entry["number"][1:]) for entry in queue], default=0) + 1
            )
            booking_number = f"A{last_number:04}"
            queue.append({"user_id": user_id, "time": timestamp, "number": booking_number})
            save_queue()
            reply = (
                "✅ *Booking Successful!* 🎉\n"
                "-----------------------------\n"
                f"🎟️ *Queue Number*: `{booking_number}`\n"
                f"🧾 *Queues Ahead*: `{len(queue) - 1}`\n"
                f"🕒 *Time*: `{datetime.fromisoformat(timestamp).strftime('%H:%M')}`\n"
                "-----------------------------"
            )

    elif msg == "cancel":
        for i, entry in enumerate(queue):
            if entry["user_id"] == user_id:
                queue.pop(i)
                save_queue()
                reply = "❌ *Your booking has been canceled.*"
                break
        else:
            reply = "⚠️ *You don't have a booking to cancel.*"

    elif msg == "queue":
        entry = next((e for e in queue if e["user_id"] == user_id), None)
        if entry:
            position = next(i for i, e in enumerate(queue) if e["user_id"] == user_id)
            if position == 0:
                reply = (
                    "🎟️ *Your Queue Number*: `{}`\n\n📌 *It's your time!!!* 🎉"
                ).format(entry['number'])
            else:
                reply = (
                    "🎟️ *Your Queue Number*: `{}`\n\n"
                    "🧾 *Queues Ahead*: `{}`"
                ).format(entry['number'], position)
        else:
            reply = "❗ *You don't have a booking yet.*\nType 'book' to reserve."

    else:
        reply = (
            "🤖 *LINE Queue Bot Commands:*\n"
            "- Type `book` to reserve a slot\n"
            "- Type `queue` to view your position\n"
            "- Type `cancel` to cancel your booking"
        )

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5050)
