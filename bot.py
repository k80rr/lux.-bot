import json
import os
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions, ChatAdministratorRights, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters
from telegram.constants import ParseMode

TOKEN = "8990345547:AAGwkM5ognSz1--Gf7Om8uYXmE3Bm-Jx2LQ"

group_settings = {}
warnings_data = {}  
last_messages = {}  

# ==================== إدارة بنك لوكس (Lux Bank) ====================
BANK_FILE = "lux_bank.json"

def load_bank():
    if os.path.exists(BANK_FILE):
        try:
            with open(BANK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_bank(data):
    with open(BANK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_bank_user(user_id, name):
    bank = load_bank()
    uid = str(user_id)
    if uid not in bank:
        bank[uid] = {
            "name": name,
            "balance": 100,  
            "last_salary": None,
            "investments": []
        }
        save_bank(bank)
    return bank[uid], bank

def get_rank(balance):
    if balance < 500:
        return "مبتدئ 🐣"
    elif balance < 2000:
        return "كاسب 💼"
    elif balance < 10000:
        return "تاجر 💰"
    elif balance < 50000:
        return "غني 💎"
    else:
        return "مليونير 👑"

# ==================== نظام الزواج الترفيهي ====================
MARRIAGE_FILE = "lux_marriages.json"

def load_marriages():
    if os.path.exists(MARRIAGE_FILE):
        try:
            with open(MARRIAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_marriages(data):
    with open(MARRIAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ==================== الوظائف المساعدة ====================
async def get_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user
    elif context.args:
        try:
            user_id = int(context.args[0])
            member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
            return member.user
        except Exception:
            return None
    return None

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    member = await context.bot.get_chat_member(chat_id, user_id)
    return member.status in ['administrator', 'creator']

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أنا بوت لوكس لإدارة وحماية الكروبات 🛡️🤖\nاكتب (لوكس لستة) لعرض لوحة الأوامر التفاعلية.")

# ==================== القائمة الرئيسية التفاعلية للأوامر ====================
def get_main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🛡️ م 1 اوامر الحماية", callback_data="menu_protection"),
            InlineKeyboardButton("👑 م 2 اوامر الادمنيه", callback_data="menu_admins")
        ],
        [
            InlineKeyboardButton("🏛️ م 3 اوامر المدراء", callback_data="menu_managers"),
            InlineKeyboardButton("🌐 م 4 اوامر المنشئين", callback_data="menu_owners")
        ],
        [
            InlineKeyboardButton("💸 م 8 اوامر البنك", callback_data="menu_bank"),
            InlineKeyboardButton("💍 م 7 اوامر التسليه", callback_data="menu_fun")
        ],
        [
            InlineKeyboardButton("🧹 م 9 اوامر التنظيف", callback_data="menu_clean"),
            InlineKeyboardButton("⚡ م 11 اوامر المطور", callback_data="menu_dev")
        ],
        [
            InlineKeyboardButton("⚙️ القفل / الفتح", callback_data="menu_locks_panel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def show_full_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = get_main_menu_keyboard()
    text = (
        "🤖 **قائمة لوحة التحكم الرئيسية - بوت لوكس:**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "اختر القسم الذي تريد استعراض أوامره من الأزرار أدناه:"
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

# ==================== لوحة التحكم بالأقفال التفاعلية ====================
async def get_settings_keyboard(chat_id):
    if chat_id not in group_settings:
        group_settings[chat_id] = {"links": False, "photos": False, "spam": False, "welcome": True}
    
    s = group_settings[chat_id]
    link_icon = "❌ مقفل" if s["links"] else "🟩 مفتوح"
    photo_icon = "❌ مقفل" if s["photos"] else "🟩 مفتوح"
    spam_icon = "❌ مقفل" if s["spam"] else "🟩 مفتوح"
    welcome_icon = "❌ مقفل" if not s["welcome"] else "🟩 مفتوح"

    keyboard = [
        [
            InlineKeyboardButton(f"الروابط : {link_icon}", callback_data="toggle_links"),
            InlineKeyboardButton(f"الصور : {photo_icon}", callback_data="toggle_photos")
        ],
        [
            InlineKeyboardButton(f"التكرار : {spam_icon}", callback_data="toggle_spam"),
            InlineKeyboardButton(f"الترحيب : {welcome_icon}", callback_data="toggle_welcome")
        ],
        [
            InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="menu_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== معالج الأزرار الشفافة ====================
async def menu_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id

    back_btn = [[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="menu_main")]]

    if data == "menu_main":
        await show_full_list(update, context)
        
    elif data == "menu_protection":
        text = (
            "🛡️ **[ م 1 ] أوامر الحماية:**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "- **قفل الروابط** / **فتح الروابط**\n"
            "- **قفل الصور** / **فتح الصور**\n"
            "- **منع التكرار** / **السماح بالتكرار**\n"
            "- حظر تلقائي عند الوصول إلى 3 تحذيرات."
        )
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(back_btn), parse_mode=ParseMode.MARKDOWN)
        
    elif data == "menu_admins":
        text = (
            "👑 **[ م 2 ] أوامر الادمنية (بالرد):**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "- **رفع مشرف** : لترقية العضو.\n"
            "- **تنزيل مشرف** : لسحب الإشراف.\n"
            "- **حظر** / **طرد** / **كتم** / **إلغاء كتم**\n"
            "- **تحذير** : إنذار العضو."
        )
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(back_btn), parse_mode=ParseMode.MARKDOWN)
        
    elif data == "menu_managers":
        text = (
            "🏛️ **[ م 3 ] أوامر المدراء:**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "- **تثبيت** : تثبيت رسالة مهمة.\n"
            "- **إحصائيات** : عرض معلومات الكروب."
        )
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(back_btn), parse_mode=ParseMode.MARKDOWN)
        
    elif data == "menu_owners":
        text = (
            "🌐 **[ م 4 ] أوامر المنشئين:**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "- التحكم الكامل بإعدادات الحماية والترحيب وصلاحيات البوت."
        )
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(back_btn), parse_mode=ParseMode.MARKDOWN)
        
    elif data == "menu_bank":
        text = (
            "💸 **[ م 8 ] أوامر بنك لوكس (Lux Bank):**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "- **فلوسي** أو **بنكي** : لعرض رصيدك ورتبتك.\n"
            "- **راتب** : استلام الراتب اليومي (500 دينار).\n"
            "- **تحويل [المبلغ]** (بالرد) : تحويل أموال.\n"
            "- **استثمار [المبلغ]** : استثمار النقود بنسبة ربح 15%."
        )
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(back_btn), parse_mode=ParseMode.MARKDOWN)
        
    elif data == "menu_fun":
        text = (
            "💍 **[ م 7 ] أوامر التسلية والزواج:**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "- **زواج** (بالرد أو المعرف) : لخطبة شخص.\n"
            "- **طلاق** : لإنهاء الارتباط.\n"
            "- **المتزوجين** : عرض قائمة الثنائيات."
        )
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(back_btn), parse_mode=ParseMode.MARKDOWN)
        
    elif data == "menu_clean":
        text = (
            "🧹 **[ م 9 ] أوامر التنظيف:**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "- **حذف** : لحذف رسالة محددة بالرد.\n"
            "- **حذف [العدد]** : لحذف عدة رسائل دفعة واحدة."
        )
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(back_btn), parse_mode=ParseMode.MARKDOWN)
        
    elif data == "menu_dev":
        text = (
            "⚡ **[ م 11 ] أوامر المطور:**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "- البوت يعمل بكفاءة عالية على مكتبة Python Telegram Bot ومزود بحماية متكاملة."
        )
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(back_btn), parse_mode=ParseMode.MARKDOWN)
        
    elif data == "menu_locks_panel":
        reply_markup = await get_settings_keyboard(chat_id)
        await query.message.edit_text("⚙️ **قائمة التحكم بالأقفال والفتح:**", reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
    elif data in ["toggle_links", "toggle_photos", "toggle_spam", "toggle_welcome"]:
        if chat_id not in group_settings:
            group_settings[chat_id] = {"links": False, "photos": False, "spam": False, "welcome": True}
            
        if data == "toggle_links":
            group_settings[chat_id]["links"] = not group_settings[chat_id]["links"]
        elif data == "toggle_photos":
            group_settings[chat_id]["photos"] = not group_settings[chat_id]["photos"]
        elif data == "toggle_spam":
            group_settings[chat_id]["spam"] = not group_settings[chat_id]["spam"]
        elif data == "toggle_welcome":
            group_settings[chat_id]["welcome"] = not group_settings[chat_id]["welcome"]
            
        new_markup = await get_settings_keyboard(chat_id)
        try:
            await query.edit_message_reply_markup(reply_markup=new_markup)
        except Exception:
            pass

# ==================== الترحيب والبنك التلقائي ====================
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            continue
        
        user_data, _ = get_bank_user(member.id, member.first_name)
        chat_id = update.effective_chat.id
        is_welcomed = group_settings.get(chat_id, {}).get("welcome", True)
        
        if is_welcomed:
            username = f"@{member.username}" if member.username else "لا يوجد"
            welcome_msg = (
                f"✨ **أهلاً بك في المجموعة!**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👤 **الاسم:** {member.mention_html()}\n"
                f"🆔 **الآيدي:** <code>{member.id}</code>\n"
                f"🌐 **المعرف:** {username}\n"
                f"🏦 **بنك لوكس:** تم فتح حساب بنكي تلقائي لك وأُضيف 100 دينار هدية ترحيبية! 💰"
            )
            await update.message.reply_text(welcome_msg, parse_mode=ParseMode.HTML)

# ==================== أوامر الزواج الترفيهي ====================
async def marry_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user
    target = await get_target_user(update, context)
    
    if not target:
        return await update.message.reply_text("يرجى الرد على رسالة الشخص الذي تريد الزواج منه.")
    if sender.id == target.id:
        return await update.message.reply_text("عذراً، لا يمكنك الزواج من نفسك! 😅")
        
    chat_id = str(update.effective_chat.id)
    marriages = load_marriages()
    if chat_id not in marriages:
        marriages[chat_id] = {}
        
    marriages[chat_id][str(sender.id)] = str(target.id)
    save_marriages(marriages)
    
    await update.message.reply_text(
        f"💍 **ألف مبروك بالرفاه والبنين!** 💐\n"
        f"🤵 {sender.mention_html()}  ⚡  👰 {target.mention_html()}",
        parse_mode=ParseMode.HTML
    )

async def divorce_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user
    chat_id = str(update.effective_chat.id)
    marriages = load_marriages()
    
    if chat_id in marriages:
        sender_id_str = str(sender.id)
        for m1, m2 in list(marriages[chat_id].items()):
            if sender_id_str == m1 or sender_id_str == m2:
                del marriages[chat_id][m1]
                save_marriages(marriages)
                return await update.message.reply_text(f"💔 **وقع الطلاق رسمياً!** العضو {sender.mention_html()} انفصل عن شريكه.", parse_mode=ParseMode.HTML)
    await update.message.reply_text("أنت غير متزوج أساساً! 🤷‍♂️")

async def list_marriages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    marriages = load_marriages()
    if chat_id not in marriages or not marriages[chat_id]:
        return await update.message.reply_text("📂 لا توجد ثنائيات مرتبطة في هذا الكروب حالياً.")
        
    text = "📜 **قائمة الثنائيات المرتبطة:**\n━━━━━━━━━━━━━━━━━━\n"
    for m1, m2 in marriages[chat_id].items():
        try:
            u1 = await context.bot.get_chat_member(update.effective_chat.id, int(m1))
            u2 = await context.bot.get_chat_member(update.effective_chat.id, int(m2))
            text += f"🤵 {u1.user.mention_html()} 🫀 👰 {u2.user.mention_html()}\n"
        except Exception:
            pass
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

# ==================== أوامر بنك لوكس ====================
async def bank_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data, _ = get_bank_user(user.id, user.first_name)
    rank = get_rank(user_data["balance"])
    await update.message.reply_text(f"🏦 **بنك لوكس:**\n👤 العضو: {user.mention_html()}\n💰 الرصيد: **{user_data['balance']}** دينار\n🎖️ الرتبة: **{rank}**", parse_mode=ParseMode.HTML)

async def bank_salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data, bank = get_bank_user(user.id, user.first_name)
    now = datetime.now()
    if user_data.get("last_salary"):
        last = datetime.fromisoformat(user_data["last_salary"])
        if now - last < timedelta(hours=24):
            rem = timedelta(hours=24) - (now - last)
            return await update.message.reply_text(f"⚠️ لقد استلمت راتبك مسبقاً! انتظر {rem.seconds // 3600} ساعة.")
    user_data["balance"] += 500
    user_data["last_salary"] = now.isoformat()
    bank[str(user.id)] = user_data
    save_bank(bank)
    await update.message.reply_text(f"✅ تم إيداع راتبك اليومي (500 دينار)! رصيدك: {user_data['balance']} 💳")

async def bank_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await update.message.reply_text("يرجى الرد على الشخص وكتابة: تحويل [المبلغ]")
    sender = update.effective_user
    receiver = update.message.reply_to_message.from_user
    args = update.message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        return await update.message.reply_text("حدد المبلغ صحيحاً (مثال: تحويل 100)")
    amount = int(args[1])
    s_data, bank = get_bank_user(sender.id, sender.first_name)
    if s_data["balance"] < amount:
        return await update.message.reply_text("رصيدك لا يكفي!")
    r_data, _ = get_bank_user(receiver.id, receiver.first_name)
    s_data["balance"] -= amount
    r_data["balance"] += amount
    bank[str(sender.id)] = s_data
    bank[str(receiver.id)] = r_data
    save_bank(bank)
    await update.message.reply_text(f"💸 تم تحويل {amount} دينار إلى {receiver.mention_html()} بنجاح!", parse_mode=ParseMode.HTML)

async def bank_invest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        return await update.message.reply_text("استخدم: استثمار [المبلغ]")
    amount = int(args[1])
    user = update.effective_user
    u_data, bank = get_bank_user(user.id, user.first_name)
    if u_data["balance"] < amount:
        return await update.message.reply_text("رصيدك لا يكفي!")
    profit = int(amount * 0.15)
    u_data["balance"] += profit
    bank[str(user.id)] = u_data
    save_bank(bank)
    await update.message.reply_text(f"📈 استثمار ناجح! ربحت +{profit} دينار. رصيدك: {u_data['balance']}")

# ==================== أوامر الإدارة ====================
async def promote_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    target = await get_target_user(update, context)
    if target:
        rights = ChatAdministratorRights(can_manage_chat=True, can_delete_messages=True, can_restrict_members=True)
        await context.bot.promote_chat_member(update.effective_chat.id, target.id, administrator_rights=rights)
        await update.message.reply_text(f"تم ترقية {target.mention_html()} مشرفاً 👑", parse_mode=ParseMode.HTML)

async def demote_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    target = await get_target_user(update, context)
    if target:
        rights = ChatAdministratorRights(can_manage_chat=False, can_delete_messages=False, can_restrict_members=False)
        await context.bot.promote_chat_member(update.effective_chat.id, target.id, administrator_rights=rights)
        await update.message.reply_text(f"تم تنزيل {target.mention_html()} من الإشراف 🔻", parse_mode=ParseMode.HTML)

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    target = await get_target_user(update, context)
    if target:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"تم حظر العضو {target.mention_html()} 🚫", parse_mode=ParseMode.HTML)

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    target = await get_target_user(update, context)
    if target:
        await context.bot.restrict_chat_member(update.effective_chat.id, target.id, permissions=ChatPermissions(can_send_messages=False))
        await update.message.reply_text(f"تم كتم العضو {target.mention_html()} 🔇", parse_mode=ParseMode.HTML)

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    target = await get_target_user(update, context)
    if target:
        await context.bot.restrict_chat_member(update.effective_chat.id, target.id, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True))
        await update.message.reply_text(f"تم إلغاء كتم العضو {target.mention_html()} 🔊", parse_mode=ParseMode.HTML)

async def pin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if update.message.reply_to_message:
        await context.bot.pin_chat_message(update.effective_chat.id, update.message.reply_to_message.message_id)
        await update.message.reply_text("تم تثبيت الرسالة بنجاح 📌")

async def delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if update.message.reply_to_message:
        await update.m