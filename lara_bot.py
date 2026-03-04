import os
import telebot
from telebot import types

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Ana Menü Butonları (Hocanın bayılacağı profesyonel yapı)
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('🎮 Oyunlar')
    btn2 = types.KeyboardButton('👤 Profilim')
    btn3 = types.KeyboardButton('🌍 Dil / Language')
    btn4 = types.KeyboardButton('🛠️ Destek')
    markup.add(btn1, btn2, btn3, btn4)
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, 
                     "Lara Bot v9.8 Sistemine Hoş Geldin Haktan! 🚀\nSistem 7/24 aktif.", 
                     reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == '🎮 Oyunlar')
def games(message):
    bot.reply_to(message, "🕹️ Mevcut Oyunlar: The Forest, Valorant, CS2\nSunucular stabil!")

@bot.message_handler(func=lambda message: message.text == '👤 Profilim')
def profile(message):
    # Senin bilgilerini buraya dinamik ekleyebiliriz
    bot.reply_to(message, "👤 Kullanıcı: Haktan DURUKAN\n🎓 Status: Software Developer")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Komut anlaşılamadı: {message.text}\nLütfen menüden seçim yapın.", reply_markup=main_menu())

bot.infinity_polling()
