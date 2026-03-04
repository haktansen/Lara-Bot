import logging
import asyncio
import httpx # type: ignore
import os
import json
from typing import List, Dict, Optional, Union, cast, Any
from deep_translator import GoogleTranslator # type: ignore
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeDefault, BotCommandScopeChat # type: ignore
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler # type: ignore

# --- AYARLAR ---
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
    },
    "es": {
        "welcome": "🚀 Lara v9.8 Hybrid Activo {name}!\n\nPuedes acceder a todos los comandos desde el menú.",
        "profil_desc": "🔔 Personaliza tus notificaciones seleccionando tus intereses:",
        "lang_select": "🌐 Por favor selecciona tu idioma:",
        "pref_saved": "✅ Tu preferencia guardada: <b>{pref}</b>",
        "lang_saved": "✅ Preferencia de idioma actualizada.",
        "listing": "🔍 Se están listando los juegos actuales...",
        "no_games": "No hay juegos gratuitos activos en la categoría '<b>{pref}</b>' actualmente.",
        "label_type": "Tipo",
        "label_price": "Precio Normal",
        "label_for_you": "Para ti",
        "label_free": "GRATIS",
        "label_rem": "Restante",
        "label_plat": "Plataforma",
        "btn_go": "🎮 Ir al juego",
        "btn_rev": "📺 Reseña",
        "auto_header": "🎁 ¡NUEVO JUEGO GRATIS!",
        "admin_no_auth": "❌ No estás autorizado para usar este comando.",
        "admin_stats": "📊 <b>PANEL DE ADMINISTRACIÓN</b>\n\n👥 Usuarios totales: {total_users}\n🎮 Juegos totales agregados: {total_games}\n📢 Anuncios enviados: {total_ann}\n\n🏆 <b>Usuarios más activos:</b>\n{user_stats}"
    },
    "de": {
        "welcome": "🚀 Lara v9.8 Hybrid Aktiv {name}!\n\nSie können auf alle Befehle über das Menü zugreifen.",
        "profil_desc": "🔔 Personalisieren Sie Ihre Benachrichtigungen, indem Sie Ihre Interessen auswählen:",
        "lang_select": "🌐 Bitte wählen Sie Ihre Sprache aus:",
        "pref_saved": "✅ Ihre Einstellung wurde gespeichert: <b>{pref}</b>",
        "lang_saved": "✅ Sprachpräferenz aktualisiert.",
        "listing": "🔍 Aktuelle Spiele werden aufgelistet...",
        "no_games": "Aktuell gibt es keine aktiven kostenlosen Spiele in der Kategorie '<b>{pref}</b>'.",
        "label_type": "Typ",
        "label_price": "Normalpreis",
        "label_for_you": "Für dich",
        "label_free": "KOSTENLOS",
        "label_rem": "Verbleibend",
        "label_plat": "Plattform",
        "btn_go": "🎮 Zum Spiel gehen",
        "btn_rev": "📺 Rezension",
        "auto_header": "🎁 NEUES KOSTENLOSES SPIEL!",
        "admin_no_auth": "❌ Sie sind nicht berechtigt, diesen Befehl zu verwenden.",
        "admin_stats": "📊 <b>ADMIN-PANEL</b>\n\n👥 Benutzer insgesamt: {total_users}\n🎮 Spiele insgesamt hinzugefügt: {total_games}\n📢 Gesendete Ankündigungen: {total_ann}\n\n🏆 <b>Aktivste Benutzer:</b>\n{user_stats}"
    },
    "ru": {
        "welcome": "🚀 Lara v9.8 Hybrid Активна {name}!\n\nВы можете получить доступ ко всем командам из меню.",
        "profil_desc": "🔔 Персонализируйте свои уведомления, выбирая свои интересы:",
        "lang_select": "🌐 Пожалуйста, выберите ваш язык:",
        "pref_saved": "✅ Ваше предпочтение сохранено: <b>{pref}</b>",
        "lang_saved": "✅ Настройки языка обновлены.",
        "listing": "🔍 Вывод текущих игр...",
        "no_games": "В категории '<b>{pref}</b>' на данный момент нет активных бесплатных игр.",
        "label_type": "Тип",
        "label_price": "Обычная цена",
        "label_for_you": "Для вас",
        "label_free": "БЕСПЛАТНО",
        "label_rem": "Осталось",
        "label_plat": "Платформа",
        "btn_go": "🎮 Перейти к игре",
        "btn_rev": "📺 Обзор",
        "auto_header": "🎁 НОВАЯ БЕСПЛАТНАЯ ИГРА!",
        "admin_no_auth": "❌ У вас нет прав на использование этой команды.",
        "admin_stats": "📊 <b>ПАНЕЛЬ АДМИНИСТРАТОРА</b>\n\n👥 Всего пользователей: {total_users}\n🎮 Всего добавлено игр: {total_games}\n📢 Отправлено объявлений: {total_ann}\n\n🏆 <b>Самые активные пользователи:</b>\n{user_stats}"
    }
}

def get_msg(key: str, lang: str = "tr") -> str:
    """Belirtilen anahtar ve dile göre mesajı döndürür."""
    lang_batch = LOCALES.get(lang, LOCALES["tr"])
    return lang_batch.get(key, LOCALES["tr"].get(key, key))

# ---------------

def _sync_translate(text: str, target: str) -> str:
    """Senkron çeviri işlemi."""
    try:
        translated = GoogleTranslator(source='auto', target=target).translate(text)
        return str(translated)
    except Exception:
        return text

async def translate_text(text: str, target_lang: str) -> str:
    """Metni belirtilen dile çevirir (Asenkron)."""
    if target_lang == 'tr' or not text:
        return text
    try:
        loop = asyncio.get_event_loop()
        translated = await loop.run_in_executor(None, _sync_translate, text, target_lang)
        return str(translated)
    except Exception as e:
        logging.error(f"Translation Error: {e}")
        return text

def load_db() -> Any:
    default_db = {
        "stats": {"total_games": 0, "total_announcements": 0, "total_savings": 0.0, "counted_games": []}, 
        "users": {}
    }
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(default_db, f, indent=4)
        return default_db
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
            if "stats" not in db: db["stats"] = default_db["stats"]
            if "users" not in db: db["users"] = {}
            return db
    except Exception as e:
        logging.error(f"Veritabani yukleme hatasi: {e}")
        return default_db
            
            # Missing keys in stats
            s = db["stats"]
            ds = default_db["stats"]
            for key in ds:
                if key not in s:
                    s[key] = ds[key]
            
            if "users" not in db:
                db["users"] = {}
            
            # Veritabanı Migrasyonu: Dil anahtarı eksik kullanıcılara ekle
            updated_db = False
            for u_id in db["users"]:
                if "language" not in db["users"][u_id]:
                    db["users"][u_id]["language"] = "tr"
                    updated_db = True
            if updated_db:
                save_db(db)
                
            return db
    except Exception as e:
        logging.error(f"Veritabani yukleme hatasi: {e}")
        return default_db

def save_db(db):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Veritabani kaydetme hatasi: {e}")

def update_user(user_id: Union[int, str], username: str, pref: Optional[str] = None):
    db: Any = load_db()
    u_id = str(user_id)
    if u_id not in db["users"]:
        db["users"][u_id] = {
            "name": username, 
            "join_date": datetime.now().strftime("%Y-%m-%d %H:%M"), 
            "preference": "Hepsi",
            "language": "tr",
            "command_count": 0
        }
    if pref:
        db["users"][u_id]["preference"] = pref
    
    # Her komut kullanımında sayacı artır
    u_ref = db["users"][u_id]
    cnt = int(u_ref.get("command_count", 0))
    u_ref["command_count"] = cnt + 1
    save_db(db)

def update_stats(game_list: Optional[List[str]] = None, price_list: Optional[List[float]] = None) -> bool:
    """
    Oyun istatistiklerini günceller. 
    """
    db: Any = load_db()
    
    if game_list and price_list:
        stats: Any = db["stats"]
        prev_counted = stats.get("counted_games", [])
        counted = [x for x in prev_counted]
        
        c_count: Any = int(stats.get("total_games", 0))
        c_savings: Any = float(stats.get("total_savings", 0.0))
        
        updated = False
        for title in game_list:
            if title not in counted:
                c_count = cast(int, c_count) + 1
                # get price for this title from price_list (same index)
                idx = game_list.index(title)
                c_savings = cast(float, c_savings) + float(price_list[idx])
                if isinstance(title, str):
                    counted.append(title)
                updated = True
        
        if updated:
            stats["total_games"] = c_count
            stats["total_savings"] = c_savings
            stats["counted_games"] = counted
            save_db(db)
            return True
    return False

# --- VERİ ÇEKME MOTORU ---
async def get_all_free_games() -> List[Dict[str, Any]]:
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=tr&country=TR&allowCountries=TR"
    all_games: List[Dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            data = response.json()
        elements = data.get('data', {}).get('Catalog', {}).get('searchStore', {}).get('elements', [])
        for game in elements:
            try:
                promotions = game.get('promotions')
                if not promotions or not (promotions.get('promotionalOffers')):
                    continue
                offers = promotions['promotionalOffers'][0].get('promotionalOffers', [])
                current_offer = next((o for o in offers if o.get('discountSetting', {}).get('discountPercentage') == 0), None)
                if not current_offer:
                    continue

                tags = [tag['name'] for tag in game.get('tags', []) if isinstance(tag, dict) and 'name' in tag]
                category = tags[0] if tags else "Genel"
                price_info = game.get('price', {}).get('totalPrice', {})
                original_price = float(price_info.get('originalPrice', 0)) / 100
                
                end_date = datetime.fromisoformat(current_offer['endDate'].replace('Z', '+00:00'))
                days_left = (end_date - datetime.now(end_date.tzinfo)).days
                countdown = f"{days_left} Gün Kaldı!" if days_left > 0 else "Bugün Son Gün!"
                
                page_slug = game.get('catalogNs', {}).get('mappings', [{}])[0].get('pageSlug', '') or game.get('productSlug', '') or game.get('urlSlug', '')
                
                all_games.append({
                    'title': game.get('title', 'Bilinmeyen Oyun'),
                    'description': game.get('description', ''),
                    'img': game.get('keyImages', [{}])[0].get('url', ''),
                    'link': f"https://store.epicgames.com/tr/p/{page_slug}",
                    'price': original_price, 'category': category, 'countdown': countdown,
                    'platform': "Epic Games 🏬", 'all_tags': [t.lower() for t in tags],
                    'yt_link': f"https://www.youtube.com/results?search_query={game['title'].replace(' ', '+')}+gameplay"
                })
            except Exception:
                continue
    except Exception as e:
        logging.error(f"API hatasi: {e}")
    return all_games

# --- BOT KOMUTLARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message:
        return
    logging.info(f"Komut alındı: /start (User: {user.id})")
    update_user(user.id, user.first_name)
    
    db: Any = load_db()
    u_lang = db["users"].get(str(user.id), {}).get("language", "tr")
    welcome_text = get_msg("welcome", u_lang).format(name=user.first_name)
    await update.message.reply_text(welcome_text)

async def profil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message:
        return
    logging.info(f"Komut alındı: /profil (User: {user.id})")
    update_user(user.id, user.first_name)
    
    db: Any = load_db()
    u_lang = db["users"].get(str(user.id), {}).get("language", "tr")
    
    keyboard = [[InlineKeyboardButton("⚔️ Aksiyon", callback_data='pref_Aksiyon'), InlineKeyboardButton("🧠 Strateji", callback_data='pref_Strateji')],
                [InlineKeyboardButton("🎭 RPG", callback_data='pref_RPG'), InlineKeyboardButton("🌍 Hepsi", callback_data='pref_Hepsi')]]
    
    await update.message.reply_text(get_msg("profil_desc", u_lang), reply_markup=InlineKeyboardMarkup(keyboard))

async def dil_sec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message:
        return
    logging.info(f"Komut alındı: /dil (User: {user.id})")
    update_user(user.id, user.first_name)
    
    db: Any = load_db()
    u_lang = db["users"].get(str(user.id), {}).get("language", "tr")
    
    keyboard = [
        [InlineKeyboardButton("Türkçe 🇹🇷", callback_data='lang_tr'), InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')],
        [InlineKeyboardButton("Spanish 🇪🇸", callback_data='lang_es'), InlineKeyboardButton("German 🇩🇪", callback_data='lang_de')],
        [InlineKeyboardButton("Russian 🇷🇺", callback_data='lang_ru')]
    ]
    await update.message.reply_text(get_msg("lang_select", u_lang), reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data or not query.from_user:
        return
    await query.answer()
    data = str(query.data)
    
    db: Any = load_db()
    u_id = str(query.from_user.id)
    u_lang = db["users"].get(u_id, {}).get("language", "tr")
    
    if data.startswith('pref_'):
        pref = data.split('_')[1]
        update_user(query.from_user.id, query.from_user.first_name, pref=pref)
        msg = get_msg("pref_saved", u_lang).format(pref=pref)
        await query.edit_message_text(text=msg, parse_mode='HTML')
    elif data.startswith('lang_'):
        lang = data.split('_')[1]
        if u_id not in db["users"]:
            update_user(query.from_user.id, query.from_user.first_name)
            db = load_db()
        db["users"][u_id]["language"] = lang
        save_db(db)
        msg = get_msg("lang_saved", lang) # New lang used for confirmation
        await query.edit_message_text(text=msg, parse_mode='HTML')

async def oyunlari_listele(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message:
        return
    logging.info(f"Komut alındı: /oyunlar (User: {user.id})")
    update_user(user.id, user.first_name)
    await update.message.reply_text("🔍 Güncel oyunlar listeleniyor...")
    games = await get_all_free_games()
    db: Any = load_db()
    users = db["users"]
    user_id_str = str(user.id)
    u_data = users.get(user_id_str, {})
    user_pref = u_data.get("preference", "Hepsi")
    user_lang = u_data.get("language", "tr")
    
    # Kategori eşleştirme tablosu (Türkçe Seçenek -> API Etiketleri)
    cat_map = {
        "Aksiyon": ["action", "aksiyon", "adventure", "macera", "shooter", "nişancı"],
        "Strateji": ["strategy", "strateji", "puzzle", "bulmaca", "card game", "kart oyunu"],
        "RPG": ["rpg", "role-playing", "rol yapma", "simulation", "simülasyon"]
    }
    
    found = False
    all_game_titles = []
    all_game_prices = []
    
    status_msg = get_msg("listing", user_lang)
    await update.message.reply_text(status_msg, parse_mode='HTML')

    for game in games:
        match = False
        if user_pref == "Hepsi":
            match = True
        else:
            required_tags = cat_map.get(user_pref, [])
            game_tags = game.get('all_tags', [])
            game_category = str(game.get('category', '')).lower()
            
            # Kategori veya etiketler içinde eşleşme kontrolü
            if any(rt in game_category for rt in required_tags) or \
               any(any(rt in tag for tag in game_tags) for rt in required_tags):
                match = True

        if match:
            found = True
            all_game_titles.append(str(game['title']))
            all_game_prices.append(float(game['price']))
            
            # Çeviriler
            t_title = await translate_text(str(game['title']), user_lang)
            t_desc = await translate_text(str(game.get('description', '')), user_lang)
            t_category = await translate_text(str(game['category']), user_lang)
            t_countdown = await translate_text(str(game['countdown']), user_lang)
            
            # Etiket Çevirileri (LOCALES Sözlüğünden)
            t_label_type = get_msg("label_type", user_lang)
            t_label_price = get_msg("label_price", user_lang)
            t_label_for_you = get_msg("label_for_you", user_lang)
            t_label_free = get_msg("label_free", user_lang)
            t_label_rem = get_msg("label_rem", user_lang)
            t_label_plat = get_msg("label_plat", user_lang)
            t_btn_go = get_msg("btn_go", user_lang)
            t_btn_rev = get_msg("btn_rev", user_lang)

            text = (
                f"🎮 <b>{t_title}</b>\n"
                f"📝 <i>{t_desc}</i>\n\n"
                f"📂 <b>{t_label_type}:</b> {t_category}\n"
                f"💰 <b>{t_label_price}:</b> {game['price']:.2f} TL\n"
                f"🎁 <b>{t_label_for_you}:</b> {t_label_free}\n"
                f"⏰ <b>{t_label_rem}:</b> {t_countdown}\n"
                f"🏢 <b>{t_label_plat}:</b> {game['platform']}"
            )
            keyboard = [[InlineKeyboardButton(t_btn_go, url=str(game['link']))], [InlineKeyboardButton(t_btn_rev, url=str(game['yt_link']))]]
            
            try:
                await update.message.reply_photo(
                    photo=str(game['img']), 
                    caption=text, 
                    reply_markup=InlineKeyboardMarkup(keyboard), 
                    parse_mode='HTML'
                )
            except Exception as e:
                logging.error(f"Mesaj gönderme hatası: {e}")
                await update.message.reply_text(f"🎮 <b>{t_title}</b>\n(Resim yüklenemedi)\n\n{text}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    if found:
        update_stats(game_list=all_game_titles, price_list=all_game_prices)
    else:
        no_games_msg = get_msg("no_games", user_lang).format(pref=user_pref)
        await update.message.reply_text(no_games_msg, parse_mode='HTML')

async def auto_check(context: ContextTypes.DEFAULT_TYPE):
    """Otomatik oyun kontrolü ve bildirim (JobQueue)."""
    logging.info("Otomatik oyun kontrolü başlatıldı...")
    games = await get_all_free_games()
    if not games:
        return
        
    db: Any = load_db()
    # stats güncellenirken dönen değer True ise yeni oyun var demektir
    all_game_titles = [str(g['title']) for g in games]
    all_game_prices = [float(g['price']) for g in games]
    
    if update_stats(game_list=all_game_titles, price_list=all_game_prices):
        logging.info("Yeni oyunlar tespit edildi! Bildirimler gönderiliyor...")
        users_dict = db["users"]
        for u_id in users_dict:
            u_data = users_dict[u_id]
            u_lang = u_data.get("language", "tr")
            u_pref = u_data.get("preference", "Hepsi")
            
            # Kategori eşleştirme (auto_check için de geçerli)
            cat_map = {
                "Aksiyon": ["action", "aksiyon", "adventure", "macera", "shooter", "nişancı"],
                "Strateji": ["strategy", "strateji", "puzzle", "bulmaca", "card game", "kart oyunu"],
                "RPG": ["rpg", "role-playing", "rol yapma", "simulation", "simülasyon"]
            }
            
            for game in games:
                match = False
                if u_pref == "Hepsi":
                    match = True
                else:
                    required_tags = cat_map.get(u_pref, [])
                    game_tags = game.get('all_tags', [])
                    game_category = str(game.get('category', '')).lower()
                    if any(rt in game_category for rt in required_tags) or \
                       any(any(rt in tag for tag in game_tags) for rt in required_tags):
                        match = True
                
                if match:
                    # Çeviriler
                    t_title = await translate_text(str(game['title']), u_lang)
                    t_desc = await translate_text(str(game.get('description', '')), u_lang)
                    t_category = await translate_text(str(game['category']), u_lang)
                    t_countdown = await translate_text(str(game['countdown']), u_lang)
                    
                    # Etiket Çevirileri (LOCALES Sözlüğünden)
                    t_alert = get_msg("auto_header", u_lang)
                    t_label_type = get_msg("label_type", u_lang)
                    t_label_price = get_msg("label_price", u_lang)
                    t_label_for_you = get_msg("label_for_you", u_lang)
                    t_label_free = get_msg("label_free", u_lang)
                    t_label_rem = get_msg("label_rem", u_lang)
                    t_btn_go = get_msg("btn_go", u_lang)

                    text = (
                        f"🚨 <b>{t_alert}</b>\n\n"
                        f"🎮 <b>{t_title}</b>\n"
                        f"📝 <i>{t_desc}</i>\n\n"
                        f"📂 <b>{t_label_type}:</b> {t_category}\n"
                        f"💰 <b>{t_label_price}:</b> {game['price']:.2f} TL\n"
                        f"🎁 <b>{t_label_for_you}:</b> {t_label_free}\n"
                        f"⏰ <b>{t_label_rem}:</b> {t_countdown}"
                    )
                    keyboard = [[InlineKeyboardButton(t_btn_go, url=str(game['link']))]]
                    
                    try:
                        await context.bot.send_photo(
                            chat_id=int(u_id), 
                            photo=str(game['img']), 
                            caption=text, 
                            reply_markup=InlineKeyboardMarkup(keyboard), 
                            parse_mode='HTML'
                        )
                        await asyncio.sleep(0.05)
                    except Exception as e:
                        logging.warning(f"Otomatik bildirim hatası (User: {u_id}): {e}")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message:
        return
    logging.info(f"Komut alındı: /admin (User: {user.id})")
    update_user(user.id, user.first_name)
    
    db: Any = load_db()
    u_lang = db["users"].get(str(user.id), {}).get("language", "tr")
    
    if user.id != ADMIN_ID:
        await update.message.reply_text(get_msg("admin_no_auth", u_lang), parse_mode='HTML')
        return
        
    stats = db["stats"]
    total_users = len(db["users"])
    total_games = int(stats.get("total_games", 0))
    total_ann = int(stats.get("total_announcements", 0))
    
    # En aktif kullanıcıları bul
    users_dict = db["users"]
    items_list: List[Any] = []
    for uid in users_dict:
        u_val = users_dict[uid]
        items_list.append([uid, u_val])
    
    # Sort
    items_list.sort(key=lambda x: int(x[1].get("command_count", 0)), reverse=True)
    
    user_stats_list: List[str] = []
    # Take first 5 manually to avoid slice error
    limit = 0
    for entry in items_list:
        if limit >= 5:
            break
        u_info = entry[1]
        user_name = str(u_info.get("name", "Bilinmeyen"))
        u_count = int(u_info.get("command_count", 0))
        # This sub-string is hard to completely localize from dictionary without complexity, 
        # but we can translate "command" word
        cmd_word = "komut" if u_lang == 'tr' else "commands"
        user_stats_list.append(f"👤 {user_name}: {u_count} {cmd_word}")
        limit = limit + 1
    user_stats = "\n".join(user_stats_list)
    
    dashboard_text = get_msg("admin_stats", u_lang).format(
        total_users=total_users,
        total_games=total_games,
        total_ann=total_ann,
        user_stats=user_stats
    )
    
    await update.message.reply_text(dashboard_text, parse_mode='HTML')

async def duyuru_yap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message:
        return
    logging.info(f"Komut alındı: /duyuru (User: {user.id})")
    update_user(user.id, user.first_name)
    
    db: Any = load_db()
    u_lang = db["users"].get(str(user.id), {}).get("language", "tr")
    
    if user.id != ADMIN_ID:
        await update.message.reply_text(get_msg("admin_no_auth", u_lang), parse_mode='HTML')
        return
    
    args = context.args or []
    msg_text = " ".join(args)
    if not msg_text:
        usage_msg = "❌ Kullanım: <code>/duyuru &lt;mesaj&gt;</code>" if u_lang == 'tr' else "❌ Usage: <code>/duyuru &lt;message&gt;</code>"
        await update.message.reply_text(usage_msg, parse_mode='HTML')
        return

    count = 0
    users_dict = db["users"]
    for u_id in users_dict:
        try:
            # Duyuru başlığı da yerelleştirilebilir ama genellikle duyuru metni öndedir
            header = "📢 <b>DUYURU:</b>" if u_lang == 'tr' else "📢 <b>ANNOUNCEMENT:</b>"
            await context.bot.send_message(chat_id=int(u_id), text=f"{header}\n\n{msg_text}", parse_mode='HTML')
            count += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            logging.warning(f"Duyuru gönderilemedi (User: {u_id}): {e}")
            continue
    
    db["stats"]["total_announcements"] = int(db["stats"].get("total_announcements", 0)) + 1
    save_db(db)
    
    success_msg = f"✅ Duyuru {count} kişiye iletildi." if u_lang == 'tr' else f"✅ Announcement sent to {count} users."
    await update.message.reply_text(success_msg, parse_mode='HTML')

# --- MENÜ AYARLARI (YENİ ÖZELLİK) ---
async def post_init(application):
    # Standart kullanıcılar için komutlar (Herkes görür)
    user_commands = [
        BotCommand("start", "Botu başlatır"),
        BotCommand("oyunlar", "Bedava oyunları listeler"),
        BotCommand("profil", "Oyun tercihlerini ayarlar"),
        BotCommand("dil", "Dil seçimini yapar / Select language")
    ]
    await application.bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
    
    # Admin için özel komutlar (Sadece siz görürsünüz)
    admin_commands = user_commands + [
        BotCommand("admin", "Yönetici paneli"),
        BotCommand("duyuru", "Kullanıcılara duyuru yap")
    ]
    await application.bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=ADMIN_ID))
    
    # Otomatik bildirim job'ını başlat (30 dakikada bir)
    application.job_queue.run_repeating(auto_check, interval=1800, first=10)
    
    logging.info("Bot komutları ve JobQueue başarıyla kaydedildi.")

# --- ANA ÇALIŞTIRICI ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profil", profil))
    app.add_handler(CommandHandler("dil", dil_sec))
    app.add_handler(CommandHandler("lang", dil_sec))
    app.add_handler(CommandHandler("oyunlar", oyunlari_listele))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("duyuru", duyuru_yap))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🚀 Lara v9.8 Hybrid Powered by DeepMind Aktif...")
    app.run_polling(drop_pending_updates=True)
