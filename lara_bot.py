import logging
import asyncio
import httpx
import os
import json
from datetime import datetime
from deep_translator import GoogleTranslator
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeChat, BotCommandScopeDefault
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# --- CONFIG ---
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') 
ADMIN_ID = 7210093343 
DB_FILE = "database.json"

# --- GENİŞLETİLMİŞ DİL VE YERELLEŞTİRME (RU, DE, FR eklendi) ---
LOCALES = {
    "tr": {
        "welcome": "🚀 Lara v9.9 Ultra Aktif {name}!",
        "listing": "🔍 Oyunlar taranıyor...",
        "label_type": "Tipo",
        "label_price": "Normal Fiyat",
        "label_free": "ÜCRETSİZ",
        "label_rem": "Kalan Süre",
        "label_plat": "Platform",
        "btn_go": "🎮 Oyuna Git",
        "btn_rev": "📺 İnceleme",
        "admin_stats": "📊 <b>Lara Dashboard</b>\n\n👥 Kayıtlı: {total_users}\n💰 Toplam Tasarruf: {savings:.2f} TL\n📢 Duyurular: {ann}"
    },
    "en": {"welcome": "🚀 Lara v9.9 Ultra Active {name}!", "label_price": "Normal Price", "label_free": "FREE", "label_rem": "Remaining", "btn_go": "🎮 Go to Game", "btn_rev": "📺 Review"},
    "ru": {"welcome": "🚀 Lara v9.9 Ultra Активен {name}!", "label_price": "Обычная цена", "label_free": "БЕСПЛАТНО", "label_rem": "осталось"},
    "de": {"welcome": "🚀 Lara v9.9 Ultra Aktiv {name}!", "label_price": "Normaler Preis", "label_free": "FREI", "label_rem": "Verbleibend"},
    "fr": {"welcome": "🚀 Lara v9.9 Ultra Actif {name}!", "label_price": "Prix Normal", "label_free": "GRATUIT", "label_rem": "Restant"}
}

# --- AKILLI VERİTABANI VE TASARRUF MOTORU ---
def load_db():
    if not os.path.exists(DB_FILE):
        return {"stats": {"total_ann": 0, "total_savings": 0.0, "counted_games": []}, "users": {}}
    with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(db, f, indent=4, ensure_ascii=False)

def update_user(user_id, name, pref=None, lang=None):
    db = load_db(); u_id = str(user_id)
    if u_id not in db["users"]:
        db["users"][u_id] = {"name": name, "preference": "Hepsi", "language": "tr", "count": 0}
    if pref: db["users"][u_id]["preference"] = pref
    if lang: db["users"][u_id]["language"] = lang
    db["users"][u_id]["count"] += 1; save_db(db)

# --- ÇEVİRİ MOTORU (Duyurular Dahil) ---
async def translate_msg(text, target):
    if target == 'tr' or not text: return text
    try:
        return await asyncio.get_event_loop().run_in_executor(None, lambda: GoogleTranslator(source='auto', target=target).translate(text))
    except: return text

# --- OYUN ÇEKME MOTORU (5 Özellik + Akıllı Tasarruf) ---
async def get_rich_games():
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=tr"
    db = load_db()
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(url)
        elements = res.json()['data']['Catalog']['searchStore']['elements']
        games = []
        for g in elements:
            try:
                promos = g['promotions']['promotionalOffers'][0]['promotionalOffers']
                if any(o['discountSetting']['discountPercentage'] == 0 for o in promos):
                    title = g['title']
                    price = float(g['price']['totalPrice']['originalPrice']) / 100
                    # Akıllı Tasarruf: Aynı oyunsa toplamı artırma
                    if title not in db["stats"]["counted_games"]:
                        db["stats"]["total_savings"] += price
                        db["stats"]["counted_games"].append(title)
                    
                    end_date = promos[0]['endDate'].split('T')[0]
                    tags = [t['name'].lower() for t in g.get('tags', [])]
                    games.append({
                        'title': title, 'desc': g['description'], 'img': g['keyImages'][0]['url'],
                        'price': price, 'rem': end_date, 'plat': "Epic Games", 'tags': tags,
                        'link': f"https://store.epicgames.com/tr/p/{g.get('productSlug', g.get('urlSlug'))}",
                        'yt': f"https://www.youtube.com/results?search_query={title.replace(' ', '+')}"
                    })
            except: continue
        save_db(db); return games

# --- KOMUTLAR ---
async def oyunlar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db(); u_id = str(update.effective_user.id)
    lang = db["users"].get(u_id, {}).get("language", "tr")
    pref = db["users"].get(u_id, {}).get("preference", "Hepsi")
    all_games = await get_rich_games()
    for g in all_games:
        # Kategori Filtreleme (FPS, Bilim Kurgu, Aksiyon eklendi)
        cat_map = {"Aksiyon": ["action", "aksiyon"], "FPS": ["fps", "shooter"], "Bilim Kurgu": ["sci-fi", "space"]}
        is_match = True if pref == "Hepsi" or any(t in g['tags'] for t in cat_map.get(pref, [])) else False
        
        if is_match:
            cap = (f"🎮 <b>{await translate_msg(g['title'], lang)}</b>\n📝 <i>{await translate_msg(g['desc'], lang)}</i>\n\n"
                   f"📂 <b>{LOCALES[lang].get('label_type', 'Tipo')}:</b> Genel\n"
                   f"💰 <b>{LOCALES[lang].get('label_price', 'Price')}:</b> {g['price']:.2f} TL\n"
                   f"🎁 <b>{LOCALES[lang].get('label_free', 'FREE')}</b>\n"
                   f"⏰ <b>{LOCALES[lang].get('label_rem', 'Rem')}:</b> {g['rem']}\n"
                   f"🏢 <b>{LOCALES[lang].get('label_plat', 'Platform')}:</b> {g['plat']}")
            kb = [[InlineKeyboardButton(LOCALES[lang]["btn_go"], url=g['link'])], [InlineKeyboardButton(LOCALES[lang]["btn_rev"], url=g['yt'])]]
            await update.message.reply_photo(photo=g['img'], caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

async def duyuru(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not context.args: return
    db = load_db(); raw_msg = " ".join(context.args)
    for u_id, data in db["users"].items():
        translated_ann = await translate_msg(raw_msg, data.get("language", "tr"))
        try: await context.bot.send_message(chat_id=int(u_id), text=f"📢 <b>{translated_ann}</b>", parse_mode='HTML')
        except: continue
    db["stats"]["total_ann"] += 1; save_db(db)

async def profil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("⚔️ Aksiyon", callback_data='p_Aksiyon'), InlineKeyboardButton("🔫 FPS", callback_data='p_FPS')],
          [InlineKeyboardButton("🚀 Bilim Kurgu", callback_data='p_Bilim Kurgu'), InlineKeyboardButton("🌍 Hepsi", callback_data='p_Hepsi')]]
    await update.message.reply_text("🔔 Kategorini seç:", reply_markup=InlineKeyboardMarkup(kb))

async def dil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("TR 🇹🇷", callback_data='l_tr'), InlineKeyboardButton("RU 🇷🇺", callback_data='l_ru')],
          [InlineKeyboardButton("DE 🇩🇪", callback_data='l_de'), InlineKeyboardButton("FR 🇫🇷", callback_data='l_fr')]]
    await update.message.reply_text("🌐 Dil seç:", reply_markup=InlineKeyboardMarkup(kb))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if q.data.startswith('p_'): update_user(q.from_user.id, q.from_user.first_name, pref=q.data.split('_')[1])
    elif q.data.startswith('l_'): update_user(q.from_user.id, q.from_user.first_name, lang=q.data.split('_')[1])
    await q.edit_message_text("✅ Güncellendi.")

async def post_init(app):
    await app.bot.set_my_commands([BotCommand("start", "Başlat"), BotCommand("oyunlar", "Listele"), BotCommand("profil", "Kategori"), BotCommand("dil", "Dil")])
    application.job_queue.run_repeating(auto_check_games, interval=3600, first=10) # Saatte bir kontrol

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("oyunlar", oyunlar)); app.add_handler(CommandHandler("duyuru", duyuru))
    app.add_handler(CommandHandler("profil", profil)); app.add_handler(CommandHandler("dil", dil))
    app.add_handler(CallbackQueryHandler(callback_handler)); app.run_polling()
