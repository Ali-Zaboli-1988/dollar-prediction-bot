import os
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from database import init_db
from utils.price_fetcher import get_instant_price
from models.predictor import get_forecast_with_sentiment
from utils.sentiment import analyze_sentiment
from utils.news_fetcher import fetch_news_from_urls, combine_news_texts

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8846427880:AAFNNe9C-UcLwIrYUVWdqF1MBESZcOyllB0')
RENDER_URL = os.getenv('RENDER_URL')  # e.g. https://your-app.onrender.com

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! به ربات پیش‌بینی دلار خوش آمدید.\n"
        "دستورات:\n"
        "/instant - قیمت لحظه‌ای دلار\n"
        "/daily - پیش‌بینی فردا\n"
        "/weekly - پیش‌بینی ۷ روز آینده"
    )

async def instant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = get_instant_price()
    await update.message.reply_text(f"💰 قیمت لحظه‌ای دلار: {price:,.0f} تومان")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # احساسات پیش‌فرض 0 (بدون خبر جدید)
    forecast = get_forecast_with_sentiment(0.0)
    await update.message.reply_text(f"📈 پیش‌بینی قیمت فردا: {forecast['tomorrow']:,.0f} تومان")

async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    forecast = get_forecast_with_sentiment(0.0)
    weekly_str = "📊 پیش‌بینی ۷ روز آینده:\n" + "\n".join([f"روز {i+1}: {p:,.0f} تومان" for i, p in enumerate(forecast['weekly'])])
    await update.message.reply_text(weekly_str)

def set_webhook(app):
    """تنظیم وب‌هوک برای ربات (در استارت Flask فراخوانی شود)"""
    if not RENDER_URL:
        print("RENDER_URL environment variable not set. Webhook not set.")
        return
    bot = Bot(token=BOT_TOKEN)
    webhook_url = f"{RENDER_URL}/webhook"
    bot.set_webhook(url=webhook_url)
    print(f"Webhook set to {webhook_url}")

def run_bot():
    """در صورت نیاز پولینگ (برای تست محلی)"""
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("instant", instant))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("weekly", weekly))
    app.run_polling()
