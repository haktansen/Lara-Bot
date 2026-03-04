import logging
import asyncio
import httpx
import os
import json
from typing import List, Dict, Optional, Union, Any
from deep_translator import GoogleTranslator
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# --- CONFIGURATION ---
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') # Kasadan çekme
ADMIN_ID = 7210093343 
DB_FILE = "database.json"

# --- LOCALIZATION (Senin v9.8 Hybrid Verilerin) ---
LOCALES = {
    "tr": {
        "welcome": "🚀 Lara v9.8 Hybrid Aktif {name}!\n\nMenüden tüm komutlara erişebilirsin.",
        "profil_desc": "🔔 Bildirimlerini kişiselleştir:",
        "lang_select": "🌐 Dil seçiminizi yapın:",
        "listing": "🔍 Güncel oyunlar listeleniyor...",
        "no_games": "Şu an aktif bir bedava oyun bulunmuyor.",
        "label_price": "Normal Fiyat",
        "label_free": "ÜCRETSİZ",
        "btn_go": "🎮 Oyuna Git",
        "btn_rev": "📺 İnceleme"
    },
    "en": {
        "welcome": "🚀 Lara v9.8 Hybrid Active {name}!",
        "profil_desc": "🔔 Personalize your notifications:",
        "lang_select": "🌐 Select language:",
        "listing": "🔍 Listing games...",
        "no_games": "No free games found currently.",
        "label_price": "Normal Price",
        "label_free": "FREE",
        "btn_go": "🎮 Go to Game",
        "btn_rev": "📺 Review"
    }
}

# --- DATABASE ENGINE ---
def load_db():
    if not os.path.exists(DB_FILE):
        return {"stats": {"total_games": 0}, "users": {}}
    with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(db, f, indent=4, ensure_ascii=False)

def update_user(user_id, username, lang="tr"):
    db = load_db()
    u_id = str(user_id)
    if u_id not in db["users"]:
        db["users"][u_id] = {"name": username, "language": lang, "command_count": 0}
    db["users"][u_id]["command_count"] += 1
    save_db(db)

# --- GAME SCRAPER ENGINE (Steam, Epic, IndieGala) ---
async def get_all_free_games():
    all_games = []
    # Epic Games API
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get("https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=tr")
            elements = res.json()['data']['Catalog']['searchStore']['elements']
            for game in elements:
                promos = game.get('promotions')
                if promos and promos.get('promotionalOffers'):
                    all_games.append({
                        'title': game['title'],
                        'link': f"https://store.epicgames.com/tr/p/{game.get('productSlug', game.get('urlSlug'))}",
                        'img': game['keyImages'][0]['url'],
                        'price': float(game['price']['totalPrice']['originalPrice']) / 100,
                        'platform': "Epic Games"
                    })
    except: pass
    
    # Steam & IndieGala (GamerPower API)
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get("https://www.gamerpower.com/api/giveaways?type=game&platform=pc")
            for g in res.json()[:3]:
                all_games.append({
                    'title': g['title'], 'link': g['open_giveaway_url'], 'img': g['image'],
                    'price': 0.0, 'platform': g['platform']
                })
    except: pass
    return all_games

# --- COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    update_user(user.id, user.first_name)
    await update.message.reply_text(LOCALES["tr"]["welcome"].format(name=user.first_name))

async def oyunlari_listele(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    update_user(user.id, user.first_name)
    await update.message.reply_text("🔍 Oyunlar taranıyor...")
    games = await get_all_free_games()
    for g in games:
        text = f"🎮 <b>{g['title']}</b>\n💰 <b>Fiyat:</b> {g['price']:.2f} TL\n🎁 <b>Durum:</b> ÜCRETSİZ\n🏢 <b>Platform:</b> {g['platform']}"
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("🎮 Oyuna Git", url=g['link'])]])
        await update.message.reply_photo(photo=g['img'], caption=text, reply_markup=markup, parse_mode='HTML')

async def post_init(application):
    await application.bot.set_my_commands([
        BotCommand("start", "Botu başlatır"),
        BotCommand("oyunlar", "Oyunları listeler"),
        BotCommand("profil", "Profil ayarları"),
        BotCommand("dil", "Dil seçimi")
    ])

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("oyunlar", oyunlari_listele))
    app.run_polling()
