# setup_webhook.py

import requests
from flask import Flask, request
from main import bot, BOT_TOKEN, types

WEBHOOK_URL = "https://image-sender-telebot.onrender.com/webhook"

app = Flask(__name__)

def process_update(update: types.Update):
    bot.process_new_updates([update])

@app.route('/webhook', methods=['POST'])
def webhook():  
    json_str = request.get_data(as_text=True)
    update = types.Update.de_json(json_str)
    process_update(update)
    return 'OK', 200

@app.route("/")
def index():
    return "Hello, World!"

def set_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    payload = {"url": WEBHOOK_URL}
    response = requests.post(url, json=payload)
    # print(response.json())

if __name__ == '__main__':
    set_webhook()
    app.run(host='0.0.0.0', port=8580)