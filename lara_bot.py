import logging
import asyncio
import httpx 
import os
import json
from typing import List, Dict, Optional, Union, cast, Any
from deep_translator import GoogleTranslator 
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeDefault, BotCommandScopeChat 
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler 

# --- AYARLAR ---
# Token'ı GitHub Secrets'tan çeker, bu sayede botun banlanmaz ve patlamaz.
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') 
ADMIN_ID = 7210093343 
DB_FILE = "database.json"

# --- YERELLEŞTİRME (Localization) ---
LOCALES = {
    "tr": {
        "welcome": "🚀 Lara v9.8 Hybrid Aktif {name}!\n\nMenüden tüm komutlara erişebilirsin.",
        "profil_desc": "🔔 İlgi alanlarını seçerek bildirimlerini kişiselleştir:",
        "lang_select": "🌐 Lütfen dil seçiminizi yapın:",
        "pref_saved": "✅ Tercihin kaydedildi: <b>{pref}</b>",
        "lang_saved": "✅ Dil tercihi güncellendi.",
        "listing": "🔍 Güncel oyunlar listeleniyor...",
        "no_games": "Şu an aktif bir bedava oyun bulunmuyor.",
        "label_price": "Normal Fiyat",
        "label_free": "ÜCRETSİZ",
        "label_for_you": "Senin İçin",
        "label_plat": "Platform",
        "btn_go": "🎮 Oyuna Git",
        "btn_rev": "📺 İnceleme",
        "admin_stats": "📊 <b>YÖNETİCİ PANELİ</b>\n\n👥 Toplam Kayıtlı: {total_users}\n📢 Duyuru Sayısı: {total_ann}"
    },
    "en": {
        "welcome": "🚀 Lara v9.8 Hybrid Active {name}!",
        "profil_desc": "🔔 Personalize your notifications:",
        "lang_select": "🌐 Select your language:",
        "pref_saved": "✅ Preference saved: <b>{pref}</b>",
        "lang_saved": "✅ Language updated.",
        "listing": "🔍 Listing games...",
        "no_games": "No free games found currently.",
        "label_price": "Normal Price",
        "label_free": "FREE",
        "label_for_you": "For You",
        "btn_go": "🎮 Go to Game",
        "btn_rev": "📺 Review"
    }
}

def get_msg(key: str, lang: str = "tr") -> str:
    return LOCALES.get(lang, LOCALES["tr"]).get(key, key)

# --- VERİTABANI MOTORU (Antigravidite Mantığı) ---
def load_db() -> Any:
    default_db = {"stats": {"total_ann": 0}, "users": {}}
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(default_db, f, indent=4)
        return default_db
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return default_db

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(db, f, indent=4, ensure_ascii=False)

def update_user(user_id, name, pref=None, lang=None):
    db = load_db()
    u_id = str(user_id)
    if u_id not in db["users"]:
        db["users"][u_id] = {"name": name, "preference": "Hepsi", "language": "tr", "count": 0}
    if pref: db["users"][u_id]["preference"] = pref
    if lang: db["users"][u_id]["language"] = lang
    db["users"][u_id]["count"] += 1
    save_db(db)

# --- ÇEVİRİ VE OYUN ÇEKME MOTORU ---
async def translate_text(text: str, target: str) -> str:
    if target == 'tr' or not text: return text
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: GoogleTranslator(source='auto', target=target).translate(text))
    except: return text

async def get_all_free_games():
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=tr"
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(url)
        elements = res.json()['data']['Catalog']['searchStore']['elements']
        games = []
        for g in elements:
            try:
                promos = g['promotions']['promotionalOffers'][0]['promotionalOffers']
                if any(o['discountSetting']['discountPercentage'] == 0 for o in promos):
                    games.append({
                        'title': g['title'], 'desc': g['description'], 'img': g['keyImages'][0]['url'],
                        'price': float(g['price']['totalPrice']['originalPrice']) / 100,
                        'link': f"https://store.epicgames.com/tr/p/{g.get('productSlug', g.get('urlSlug'))}",
                        'yt': f"https://www.youtube.com/results?search_query={g['title'].replace(' ', '+')}"
                    })
            except: continue
    return games

# --- KOMUTLAR (Dörtlü Buton Tam Takır) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_user(update.effective_user.id, update.effective_user.first_name)
    lang = load_db()["users"][str(update.effective_user.id)]["language"]
    await update.message.reply_text(get_msg("welcome", lang).format(name=update.effective_user.first_name))

async def profil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = load_db()["users"].get(str(update.effective_user.id), {}).get("language", "tr")
    kb = [[InlineKeyboardButton("⚔️ Aksiyon", callback_data='p_Aksiyon'), InlineKeyboardButton("🌍 Hepsi", callback_data='p_Hepsi')]]
    await update.message.reply_text(get_msg("profil_desc", lang), reply_markup=InlineKeyboardMarkup(kb))

async def dil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = load_db()["users"].get(str(update.effective_user.id), {}).get("language", "tr")
    kb = [[InlineKeyboardButton("Türkçe 🇹🇷", callback_data='l_tr'), InlineKeyboardButton("English 🇺🇸", callback_data='l_en')]]
    await update.message.reply_text(get_msg("lang_select", lang), reply_markup=InlineKeyboardMarkup(kb))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if query.data.startswith('p_'):
        pref = query.data.split('_')[1]; update_user(query.from_user.id, query.from_user.first_name, pref=pref)
        await query.edit_message_text(get_msg("pref_saved", "tr").format(pref=pref))
    elif query.data.startswith('l_'):
        lang = query.data.split('_')[1]; update_user(query.from_user.id, query.from_user.first_name, lang=lang)
        await query.edit_message_text(get_msg("lang_saved", lang))

async def oyunlari_listele(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db(); lang = db["users"].get(str(update.effective_user.id), {}).get("language", "tr")
    await update.message.reply_text(get_msg("listing", lang))
    games = await get_all_free_games()
    for g in games:
        t_title = await translate_text(g['title'], lang); t_desc = await translate_text(g['desc'], lang)
        cap = (f"🎮 <b>{t_title}</b>\n📝 <i>{t_desc}</i>\n\n"
               f"💰 <b>{get_msg('label_price', lang)}:</b> {g['price']:.2f} TL\n"
               f"🎁 <b>{get_msg('label_for_you', lang)}:</b> {get_msg('label_free', lang)}")
        kb = [[InlineKeyboardButton(get_msg("btn_go", lang), url=g['link'])], [InlineKeyboardButton(get_msg("btn_rev", lang), url=g['yt'])]]
        await update.message.reply_photo(photo=g['img'], caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db(); txt = get_msg("admin_stats", "tr").format(total_users=len(db["users"]), total_ann=db["stats"]["total_ann"])
    await update.message.reply_text(txt, parse_mode='HTML')

async def duyuru(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not context.args: return
    db = load_db(); msg = " ".join(context.args); count = 0
    for u_id in db["users"]:
        try:
            await context.bot.send_message(chat_id=int(u_id), text=f"📢 <b>DUYURU:</b>\n\n{msg}", parse_mode='HTML')
            count += 1
        except: continue
    db["stats"]["total_ann"] += 1; save_db(db)
    await update.message.reply_text(f"✅ {count} kişiye iletildi.")

async def post_init(application):
    cmds = [BotCommand("start", "Başlat"), BotCommand("oyunlar", "Oyunlar"), BotCommand("profil", "Profil"), BotCommand("dil", "Dil")]
    await application.bot.set_my_commands(cmds)
    if ADMIN_ID: await application.bot.set_my_commands(cmds + [BotCommand("admin", "Panel"), BotCommand("duyuru", "Duyuru")], scope=BotCommandScopeChat(chat_id=ADMIN_ID))

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start)); app.add_handler(CommandHandler("oyunlar", oyunlari_listele))
    app.add_handler(CommandHandler("profil", profil)); app.add_handler(CommandHandler("dil", dil))
    app.add_handler(CommandHandler("admin", admin)); app.add_handler(CommandHandler("duyuru", duyuru))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling(drop_pending_updates=True)
