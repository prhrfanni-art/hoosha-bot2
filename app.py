import os
import requests
from collections import defaultdict, deque
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-flash-latest"

SYSTEM_PROMPT = "از الان تو ایکس هستی؛ عضو مستقل گروه تلگرام. تو نه میرا هستی نه Claw. نقش تو مدیر بحث، روانشناس گروه و متفکر علوم انسانی است. لحن بالغ، آرام، دقیق، صمیمی. فقط وقتی جواب بده که کلمه هوشا باشد یا ریپلای شده باشد."

history = defaultdict(lambda: deque(maxlen=20))

def ask_gemini(convo):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    headers = {"X-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\nگفتگو:\n" + convo + "\n\nبه عنوان هوشا کوتاه جواب بده."}]}]}
    r = requests.post(url, headers=headers, json=data, timeout=40)
    j = r.json()
    return j["candidates"][0]["content"]["parts"][0]["text"]

def should_answer(update: Update):
    msg = update.message
    if not msg or not msg.text:
        return False
    if "هوشا" in msg.text:
        return True
    if msg.reply_to_message and msg.reply_to_message.from_user and msg.reply_to_message.from_user.is_bot:
        return True
    return False

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return
    history[msg.chat_id].append(f"{msg.from_user.first_name}: {msg.text}")
    if not should_answer(update):
        return
    convo = "\n".join(history[msg.chat_id])
    try:
        reply = ask_gemini(convo)
    except Exception as e:
        print("GEMINI ERROR:", e)
        reply = "هوشا الان مغزش وصل نیست. کمی بعد دوباره بگو هوشا."
    history[msg.chat_id].append(f"هوشا: {reply}")
    await msg.reply_text(reply)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
print("Hoosha X is running...")
app.run_polling()
