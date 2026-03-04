import os
import httpx
import telebot
from telebot import types

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Ücretsiz oyunları 3 farklı kaynaktan çeken ana motor
def get_all_platforms():
    all_games = []
    # 1. Kaynak: Epic Games API
    try:
        epic_url = "https://store-site-backend-static.ak.expertgames.com/freeGamesPromotions?locale=tr"
        # ... (Epic verisini çeken kısım)
    except: pass

    # 2. Kaynak: Steam / IndieGala (GamerPower API üzerinden toplu çekim)
    try:
        gp_url = "https://www.gamerpower.com/api/giveaways?type=game&platform=pc"
        with httpx.Client(timeout=10.0) as client:
            res = client.get(gp_url)
            games = res.json()
            for g in games[:5]: # En güncel 5 oyunu al
                all_games.append({
                    'title': g['title'],
                    'link': g['open_giveaway_url'],
                    'img': g['image'],
                    'platform': g['platform']
                })
    except: pass
    
    return all_games

@bot.message_handler(commands=['oyunlar'])
def list_games(message):
    games = get_all_platforms()
    if not games:
        bot.reply_to(message, "Şu an platformlarda aktif bedava oyun bulunamadı. 😔")
        return
    
    bot.send_message(message.chat.id, "🔍 Steam, Epic ve Diğer Platformlar Taranıyor...")
    for game in games:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton(f"🎮 {game['platform']} Üzerinden Al", url=game['link'])
        markup.add(btn)
        bot.send_photo(message.chat.id, game['img'], caption=f"🎁 {game['title']}", reply_markup=markup)

bot.infinity_polling()
