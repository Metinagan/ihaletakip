from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re

TOKEN = '7765375205:AAH_96Ni4Hg_2FRNEMXI7XPwJJVzK6kH6Is'
#chat_id = '1018512971'  # Bu satırı kaldırın, artık chat_id kullanıcıdan alınacak.

# Kullanıcı chat_id'lerini saklamak için bir set oluşturun
users = set()

def get_price():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    url = 'https://eihale.gov.tr/ihaleler/detay/u6kRme2QFvHWwpcJdpJ17L'
    driver.get(url)

    try:
        current_price_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'current-price')))
        price_span = current_price_div.find_element(By.CLASS_NAME, 'mx-2')
        price_text = price_span.text.strip()

        numbers_only = re.sub(r'[^\d,]', '', price_text)
        
        driver.quit()
        return numbers_only

    except Exception as e:
        driver.quit()
        print(f"Fiyat bulunamadı: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Yeni kullanıcıyı kaydet
    users.add(update.message.chat.id)
    
    # Kullanıcıya botun çalışmaya başladığını bildir
    await update.message.reply_text("Bot aktif! Fiyat takibi başlıyor.")
    
    # Arka planda fiyat kontrol görevini başlat
    if 'price_task' not in context.application.chat_data:
        context.application.chat_data['price_task'] = asyncio.create_task(check_price(context.application))

async def check_price(app: Application):
    last_price = ""
    while True:
        # Selenium işlemlerini bir thread pool'da çalıştır
        price = await asyncio.get_event_loop().run_in_executor(None, get_price)
        if price:
            if price != last_price:
                last_price = price
                # Fiyat değişikliği olduğunda tüm kullanıcılara mesaj gönder
                for user_id in users:
                    await app.bot.send_message(chat_id=user_id, text=f"Güncel Fiyat: {price}")
        await asyncio.sleep(60)

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    try:
        while True:
            await asyncio.sleep(3600)  # Uygulamayı açık tut
    except asyncio.CancelledError:
        pass
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
