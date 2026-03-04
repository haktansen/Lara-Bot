import os
import telebot

# Bot tokenini GitHub Secrets üzerinden güvenli bir şekilde alacağız
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Merhaba! Ben Lara Bot v9.8. 🚀\n7/24 bulut üzerinde çalışıyorum.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Mesajını aldım: " + message.text)

if __name__ == "__main__":
    bot.infinity_polling()
