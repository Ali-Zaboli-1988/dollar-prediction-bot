from datetime import datetime, timedelta
from typing import List, Tuple
from database import get_history
import numpy as np

def predict_daily_price(sentiment_boost: float = 0.0) -> float:
    """پیش‌بینی قیمت فردا بر اساس رگرسیون خطی روی ۵ روز اخیر + تاثیر احساسات"""
    history = get_history(10)
    if len(history) < 3:
        # داده کافی نیست، از آخرین قیمت + 1% استفاده کن
        last_price = get_history(1)
        if last_price:
            return last_price[0][1] * (1 + sentiment_boost * 0.02)
        return 60000  # fallback
    
    # استخراج قیمت‌ها و روزها (شاخص روز)
    dates = [i for i in range(len(history))]
    prices = [h[1] for h in history]
    
    # رگرسیون خطی ساده
    z = np.polyfit(dates, prices, 1)
    p = np.poly1d(z)
    next_day = len(history)  # شاخص فردا
    linear_pred = p(next_day)
    
    # اعمال احساسات (هر 0.1 احساسات حدود 0.5% تغییر)
    sentiment_effect = 1 + (sentiment_boost * 0.05)  # مثبت = کاهش قیمت
    final_pred = linear_pred * sentiment_effect
    return max(10000, final_pred)  # حداقل ۱۰ هزار تومان

def predict_weekly(prices: List[float]) -> List[float]:
    """پیش‌بینی ۷ روز آینده با استفاده از میانگین متحرک و نوسان اخیر"""
    if len(prices) < 3:
        base = prices[-1] if prices else 60000
        return [base * (1 + 0.005*i) for i in range(1,8)]
    
    changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    avg_change = np.mean(changes)
    last_price = prices[-1]
    predictions = []
    for i in range(1, 8):
        pred = last_price + avg_change * i
        # جلوگیری از اعداد غیرمنطقی
        pred = max(10000, min(300000, pred))
        predictions.append(pred)
    return predictions

def get_forecast_with_sentiment(sentiment: float) -> dict:
    """
    بازگشت:
    - price_today: قیمت لحظه‌ای امروز (از دیتابیس یا API)
    - price_tomorrow: پیش‌بینی فردا
    - weekly_forecast: لیست ۷ روز آینده
    """
    from utils.price_fetcher import get_instant_price
    instant = get_instant_price()
    tomorrow_price = predict_daily_price(sentiment)
    
    history = get_history(30)
    past_prices = [h[1] for h in history if h[1] > 0]
    if not past_prices:
        past_prices = [instant]
    weekly = predict_weekly(past_prices)
    
    # تنظیم هفتگی با احساسات کلی
    sentiment_factor = 1 - sentiment * 0.1  # مثبت = کاهش قیمت
    weekly = [p * sentiment_factor for p in weekly]
    
    return {
        'instant': round(instant, 0),
        'tomorrow': round(tomorrow_price, 0),
        'weekly': [round(p, 0) for p in weekly]
    }
