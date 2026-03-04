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
# Token'ı GitHub Secrets üzerinden güvenle çeker
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') 
ADMIN_ID = 7210093343 
DB_FILE = "database.json"

# --- YERELLEŞTİRME (LOCALIZATION) ---
LOCALES = {
    "tr": {
        "welcome": "🚀 Lara v9.8 Hybrid Aktif {name}!\n\nMenüden tüm komutlara erişebilirsin.",
        "profil_desc": "🔔 İlgi alanlarını seçerek bildirimlerini kişiselleştir:",
        "lang_select": "🌐 Lütfen dil seçiminizi yapın:",
        "pref_saved": "✅ Tercihin kaydedildi: <b>{pref}</b>",
        "lang_saved": "✅ Dil tercihi güncellendi.",
        "listing": "🔍 Güncel oyunlar listeleniyor...",
        "no_games": "Şu an '<b>{pref}</b>' kategorisinde aktif bir bedava oyun bulunmuyor.",
        "label_type": "Tür",
        "label_price": "Normal Fiyat",
        "label_for_you": "Senin İçin",
        "label_free": "ÜCRETSİZ",
        "label_rem": "Kalan",
        "label_plat": "Platform",
        "btn_go": "🎮 Oyuna Git",
        "btn_rev": "📺 İnceleme",
        "auto_header": "🎁 YENİ BEDAVA OYUN!",
        "admin_no_auth": "❌ Bu komutu kullanmaya yetkiniz yok.",
        "admin_stats": "📊 <b>YÖNETİCİ PANELİ</b>\n\n👥 Toplam Kayıtlı: {total_users}\n🎮 Eklenen Toplam Oyun: {total_games}\n📢 Gönderilen Duyuru: {total_ann}\n\n🏆 <b>En Aktif Kullanıcılar:</b>\n{user_stats}"
    },
    "en": {
        "welcome": "🚀 Lara v9.8 Hybrid Active {name}!\n\nYou can access all commands from the menu.",
        "profil_desc": "🔔 Personalize your notifications by selecting your interests:",
        "lang_select": "🌐 Please select your language:",
        "pref_saved": "✅ Your preference saved: <b>{pref}</b>",
        "lang_saved": "✅ Language preference updated.",
        "listing": "🔍 Current games are being listed...",
        "no_games": "There are no active free games in the '<b>{pref}</b>' category currently.",
        "label_type": "Type",
        "label_price": "Normal Price",
        "label_for_you": "For You",
        "label_free": "FREE",
        "label_rem": "Remaining",
        "label_plat": "Platform",
        "btn_go": "🎮 Go to Game",
        "btn_rev": "📺 Review",
        "auto_header": "🎁 NEW FREE GAME!",
        "admin_no_auth": "❌ You are not authorized to use this command.",
        "admin_stats": "📊 <b>ADMIN PANEL</b>\n\n👥 Total Users: {total_users}\n🎮 Total Games Added: {total_games}\n📢 Announcements Sent: {total_ann}\n\n🏆 <b>Most Active Users:</b>\n{user_stats}"
    }
}

def get_msg(key: str, lang: str = "tr") -> str:
    lang_batch = LOCALES.get(lang, LOCALES["tr"])
    return lang_batch.get(key, LOCALES["tr"].get(key, key))

def _sync_translate(text: str, target: str) -> str:
    try:
        translated = GoogleTranslator(source='auto', target=target).translate(text)
        return str(translated)
    except Exception: return text

async def translate_text(text: str, target_lang: str) -> str:
    if target_lang == 'tr' or not text: return text
    try:
        loop = asyncio.get_event_loop()
        translated = await loop.run_in_executor(None, _sync_translate, text, target_lang)
        return str(translated)
    except Exception as e:
        logging.error(f"Translation Error: {e}")
        return text

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- VERİTABANI MOTORU ---
def load_db() -> Any:
    default_db = {"stats": {"total_games": 0, "total_announcements": 0, "total_savings": 0.0, "counted_games": []}, "users": {}}
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(default_db, f, indent=4)
        return default_db
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return default_db

def save_db(db):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(db, f, indent=4, ensure_ascii=False)
    except Exception as e: logging.error(f"Veritabani kaydetme hatasi: {e}")

def update_user(user_id: Union[int, str], username: str, pref: Optional[str] = None):
    db = load_db()
    u_id = str(user_id)
    if u_id not in db["users"]:
        db["users"][u_id] = {"name": username, "join_date": datetime.now().strftime("%Y-%m-%d %H:%M"), "preference": "Hepsi", "language": "tr", "command_count": 0}
    if pref: db["users"][u_id]["preference"] = pref
    db["users"][u_id]["command_count"] += 1
    save_db(db)

# --- VERİ ÇEKME MOTORU (Epic Games) ---
async def get_all_free_games() -> List[Dict[str, Any]]:
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=tr&country=TR&allowCountries=TR"
    all_games = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            data = response.json()
        elements = data.get('data', {}).get('Catalog', {}).get('searchStore', {}).get('elements', [])
        for game in elements:
            try:
                promotions = game.get('promotions')
                if not promotions or not promotions.get('promotionalOffers'): continue
                offers = promotions['promotionalOffers'][0].get('promotionalOffers', [])
                if not any(o.get('discountSetting', {}).get('discountPercentage') == 0 for o in offers): continue
                
                tags = [tag['name'] for tag in game.get('tags', []) if isinstance(tag, dict) and 'name' in tag]
                price_info = game.get('price', {}).get('totalPrice', {})
                
                all_games.append({
                    'title': game.get('title', 'Bilinmeyen Oyun'),
                    'description': game.get('description', ''),
                    'img': game.get('keyImages', [{}])[0].get('url', ''),
                    'link': f"https://store.epicgames.com/tr/p/{game.get('productSlug', game.get('urlSlug'))}",
                    'price': float(price_info.get('originalPrice', 0)) / 100,
                    'category': tags[0] if tags else "Genel",
                    'platform': "Epic Games 🏬",
                    'yt_link': f"https://www.youtube.com/results?search_query={game['title'].replace(' ', '+')}+gameplay"
                })
            except: continue
    except Exception as e: logging.error(f"API hatasi: {e}")
    return all_games

# --- BOT KOMUTLARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    update_user(user.id, user.first_name)
    u_lang = load_db()["users"].get(str(user.id), {}).get("language", "tr")
    await update.message.reply_text(get_msg("welcome", u_lang).format(name=user.first_name))

async def oyunlari_listele(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    update_user(user.id, user.first_name)
    db = load_db()
    u_lang = db["users"].get(str(user.id), {}).get("language", "tr")
    
    await update.message.reply_text(get_msg("listing", u_lang))
    games = await get_all_free_games()
    
    for game in games:
        t_title = await translate_text(game['title'], u_lang)
        t_desc = await translate_text(game['description'], u_lang)
        text = (f"🎮 <b>{t_title}</b>\n📝 <i>{t_desc}</i>\n\n"
                f"💰 <b>{get_msg('label_price', u_lang)}:</b> {game['price']:.2f} TL\n"
                f"🎁 <b>{get_msg('label_for_you', u_lang)}:</b> {get_msg('label_free', u_lang)}\n"
                f"🏢 <b>{get_msg('label_plat', u_lang)}:</b> {game['platform']}")
        
        keyboard = [[InlineKeyboardButton(get_msg("btn_go", u_lang), url=game['link'])],
                    [InlineKeyboardButton(get_msg("btn_rev", u_lang), url=game['yt_link'])]]
        
        await update.message.reply_photo(photo=game['img'], caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

async def post_init(application):
    user_commands = [BotCommand("start", "Botu başlatır"), BotCommand("oyunlar", "Bedava oyunları listeler")]
    await application.bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
    # Otomatik kontrol (JobQueue) - Antigravidite mantığı
    # application.job_queue.run_repeating(auto_check, interval=1800, first=10)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("oyunlar", oyunlari_listele))
    print("🚀 Lara v9.8 Hybrid Aktif...")
    app.run_polling(drop_pending_updates=True)
