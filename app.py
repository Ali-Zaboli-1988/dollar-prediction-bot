from flask import Flask, request, render_template, jsonify
import os
from apscheduler.schedulers.background import BackgroundScheduler
from database import init_db, update_sentiment_for_today, get_latest_price
from utils.price_fetcher import fetch_and_store_daily, get_instant_price
from utils.news_fetcher import fetch_news_from_urls, combine_news_texts
from utils.sentiment import analyze_sentiment
from models.predictor import get_forecast_with_sentiment
from bot import set_webhook
from telegram import Bot, Update
import asyncio

app = Flask(__name__)

# مقداردهی اولیه دیتابیس
init_db()

# زمانبندی: هر روز ساعت 00:05 قیمت روزانه را بگیر و ذخیره کن
scheduler = BackgroundScheduler()
scheduler.add_job(func=fetch_and_store_daily, trigger="cron", hour=0, minute=5)
scheduler.start()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        urls_text = request.form.get('urls', '')
        urls = [u.strip() for u in urls_text.split('\n') if u.strip()]
        if not urls:
            return render_template('index.html', error='حداقل یک لینک وارد کنید')
        
        # دریافت و ترکیب اخبار
        news_list = fetch_news_from_urls(urls)
        full_text = combine_news_texts(news_list)
        sentiment = analyze_sentiment(full_text)
        
        # ذخیره احساسات امروز در دیتابیس
        update_sentiment_for_today(sentiment)
        
        # دریافت پیش‌بینی‌ها با احساسات جدید
        forecast = get_forecast_with_sentiment(sentiment)
        
        return render_template('index.html',
                               news_count=len(news_list),
                               sentiment=f"{sentiment:.2f}",
                               instant=forecast['instant'],
                               tomorrow=forecast['tomorrow'],
                               weekly=forecast['weekly'])
    
    # GET: نمایش فرم
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    """وب‌هوک ربات تلگرام"""
    try:
        bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN', '8846427880:AAFNNe9C-UcLwIrYUVWdqF1MBESZcOyllB0'))
        update = Update.de_json(request.get_json(force=True), bot)
        # پردازش آپدیت به صورت غیرهمزمان
        asyncio.create_task(handle_update(update, bot))
        return 'ok', 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return 'error', 500

async def handle_update(update: Update, bot: Bot):
    """مدیریت دستورات ربات"""
    if not update.message:
        return
    text = update.message.text
    chat_id = update.message.chat_id
    
    if text == '/start':
        await bot.send_message(chat_id, "سلام! من ربات پیش‌بینی دلار هستم.\n/instant - قیمت لحظه‌ای\n/daily - پیش‌بینی فردا\n/weekly - پیش‌بینی هفتگی")
    elif text == '/instant':
        price = get_instant_price()
        await bot.send_message(chat_id, f"💰 قیمت لحظه‌ای دلار: {price:,.0f} تومان")
    elif text == '/daily':
        forecast = get_forecast_with_sentiment(0.0)
        await bot.send_message(chat_id, f"📈 پیش‌بینی قیمت فردا: {forecast['tomorrow']:,.0f} تومان")
    elif text == '/weekly':
        forecast = get_forecast_with_sentiment(0.0)
        weekly_str = "📊 پیش‌بینی ۷ روز آینده:\n" + "\n".join([f"روز {i+1}: {p:,.0f} تومان" for i, p in enumerate(forecast['weekly'])])
        await bot.send_message(chat_id, weekly_str)
    else:
        await bot.send_message(chat_id, "دستور نامعتبر. از /start راهنما بگیرید.")

# هنگام شروع، وب‌هوک تلگرام را تنظیم کن
with app.app_context():
    set_webhook(app)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
