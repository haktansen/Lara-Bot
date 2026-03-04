import os
import telebot
from telebot import types

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    # Buton metinlerini daha sade tutalım ki kodla tam eşleşsin
    markup.add('🎮 Oyunlar', '👤 Profilim', '🌍 Dil / Language', '🛠️ Destek')
    return markup

@bot.message_handler(commands=['start', 'help'])
def welcome(message):
    bot.send_message(message.chat.id, 
                     "Lara Bot v9.8 Sistemine Hoş Geldin Haktan! 🚀\nSistem 7/24 aktif.", 
                     reply_markup=main_menu())

# HEM komutla (/oyunlar) HEM DE butonla (🎮 Oyunlar) çalışması için:
@bot.message_handler(func=lambda message: message.text == '🎮 Oyunlar' or message.text == '/oyunlar')
def games(message):
    bot.reply_to(message, "🕹️ Mevcut Oyunlar: The Forest, Valorant, CS2\nSunucular stabil!")

@bot.message_handler(func=lambda message: message.text == '👤 Profilim' or message.text == '/profil')
def profile(message):
    bot.reply_to(message, "👤 Kullanıcı: Haktan DURUKAN\n🎓 Status: Software Developer\n📍 Konum: Bayburt")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    # Eğer yukarıdakilerle eşleşmezse bu çalışır
    bot.reply_to(message, f"Komut anlaşılamadı: {message.text}\nLütfen menüdeki butonları kullanın.", reply_markup=main_menu())

bot.infinity_polling()
