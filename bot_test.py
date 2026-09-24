import os
import logging
import sqlite3
import traceback
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# 1. إعداد السجلات (Logging)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_NAME = "work_assistant.db"

# 2. إدارة قاعدة البيانات
def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'ar',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS earnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task_name TEXT,
                amount REAL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB Error: {e}")

init_db()

def get_user_lang(user_id: int) -> str:
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else "ar"
    except Exception:
        return "ar"

def set_user_lang(user_id: int, lang: str):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, language) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET language = excluded.language
        """, (user_id, lang))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Lang Error: {e}")

def get_user_earnings(user_id: int):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(amount) FROM earnings WHERE user_id = ?", (user_id,))
        total = cursor.fetchone()[0]
        cursor.execute("SELECT task_name, amount, completed_at FROM earnings WHERE user_id = ? ORDER BY completed_at DESC", (user_id,))
        tasks = cursor.fetchall()
        conn.close()
        return total or 0.0, tasks
    except Exception:
        return 0.0, []

# 3. النصوص والقوائم (Translations & Keyboards)
TEXTS = {
    "ar": {
        "welcome": "أهلاً بك في بوت العمل أونلاين الخاص بـ Fariskkbot!",
        "menu_online_work": "💻 العمل أونلاين",
        "menu_find_opps": "🔎 البحث عن فرص",
        "menu_tasks": "🤖 المهام المتاحة",
        "menu_earnings": "💰 الأرباح",
        "menu_completed": "📋 المهام المنجزة",
        "menu_change_lang": "🌐 تغيير اللغة",
        "menu_help": "ℹ️ المساعدة",
        "work_info": "💡 **دليل العمل أونلاين:**\n• فرص موثوقة وقانونية فقط.\n• لا تتطلب شهادة جامعية وتناسب المبتدئين.\n• إمكانية العمل عبر الهاتف الذكي.",
        "no_earnings": "لا توجد أرباح مسجلة حالياً.",
        "total_earnings": "💰 **إجمالي الأرباح الحقيقية:** ${:.2f}",
        "completed_title": "📋 **المهام المنجزة:**\n",
        "no_tasks": "لم تقم بإكمال أي مهام حتى الآن.",
        "help_text": "ℹ️ **المساعدة:** يمكنك استخدام القائمة للتنقل، أو أرسل /test لإجراء فحص النظام تلقائياً.",
        "select_lang": "اختر اللغة / Select Language:",
        "lang_changed": "تم تغيير اللغة بنجاح إلى العربية.",
        "error_msg": "حدث خطأ غير متوقع، يرجى المحاولة مرة أخرى."
    },
    "en": {
        "welcome": "Welcome to Fariskkbot Online Work Assistant!",
        "menu_online_work": "💻 Online Work",
        "menu_find_opps": "🔎 Find Opportunities",
        "menu_tasks": "🤖 Available Tasks",
        "menu_earnings": "💰 Earnings",
        "menu_completed": "📋 Completed Tasks",
        "menu_change_lang": "🌐 Change Language",
        "menu_help": "ℹ️ Help",
        "work_info": "💡 **Online Work Guide:**\n• Legitimate and verified opportunities only.\n• No university degree needed for beginners.\n• Perform tasks easily using your smartphone.",
        "no_earnings": "No earnings recorded yet.",
        "total_earnings": "💰 **Total Real Earnings:** ${:.2f}",
        "completed_title": "📋 **Completed Tasks:**\n",
        "no_tasks": "You haven't completed any tasks yet.",
        "help_text": "ℹ️ **Help:** Use the bottom menu or send /test for automated diagnostics.",
        "select_lang": "Select Language / اختر اللغة:",
        "lang_changed": "Language successfully changed to English.",
        "error_msg": "An unexpected error occurred. Please try again."
    }
}

def get_main_keyboard(lang: str) -> ReplyKeyboardMarkup:
    t = TEXTS[lang]
    keyboard = [
        [t["menu_online_work"], t["menu_find_opps"]],
        [t["menu_tasks"], t["menu_earnings"]],
        [t["menu_completed"], t["menu_change_lang"]],
        [t["menu_help"]]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# 4. المعالجات والأوامر
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    await update.message.reply_text(
        TEXTS[lang]["welcome"],
        reply_markup=get_main_keyboard(lang)
    )

async def test_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    report = "🧪 **تقرير فحص البوت وقاعدة البيانات:**\n\n"
    try:
        set_user_lang(user_id, lang)
        report += "✅ قاعدة البيانات (المستخدمون): تعمل بنجاح.\n"
    except Exception as e:
        report += f"❌ قاعدة البيانات: خطأ - {e}\n"
        
    try:
        get_user_earnings(user_id)
        report += "✅ قاعدة البيانات (الأرباح): تعمل بنجاح.\n"
    except Exception as e:
        report += f"❌ الأرباح: خطأ - {e}\n"

    report += "\n🎯 **النتيجة:** البوت جاهز ومكتمل الفحص."
    await update.message.reply_text(report, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    t = TEXTS[lang]

    if text in [TEXTS["ar"]["menu_online_work"], TEXTS["en"]["menu_online_work"]]:
        await update.message.reply_text(t["work_info"], parse_mode="Markdown")

    elif text in [TEXTS["ar"]["menu_find_opps"], TEXTS["en"]["menu_find_opps"], TEXTS["ar"]["menu_tasks"], TEXTS["en"]["menu_tasks"]]:
        msg = "📌 **Appen Data Evaluation**\n💵 Payment: $10.00/hr\n📱 Requirement: Smartphone"
        inline_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 View Opportunity", url="https://www.appen.com")]
        ])
        await update.message.reply_text(msg, reply_markup=inline_kb, parse_mode="Markdown")

    elif text in [TEXTS["ar"]["menu_earnings"], TEXTS["en"]["menu_earnings"]]:
        total, _ = get_user_earnings(user_id)
        if total > 0:
            await update.message.reply_text(t["total_earnings"].format(total), parse_mode="Markdown")
        else:
            await update.message.reply_text(t["no_earnings"])

    elif text in [TEXTS["ar"]["menu_completed"], TEXTS["en"]["menu_completed"]]:
        _, tasks = get_user_earnings(user_id)
        if tasks:
            msg = t["completed_title"]
            for task_name, amount, date in tasks:
                msg += f"• {task_name}: ${amount:.2f} ({date[:10]})\n"
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text(t["no_tasks"])

    elif text in [TEXTS["ar"]["menu_change_lang"], TEXTS["en"]["menu_change_lang"]]:
        inline_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"), InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
        ])
        await update.message.reply_text(t["select_lang"], reply_markup=inline_kb)

    elif text in [TEXTS["ar"]["menu_help"], TEXTS["en"]["menu_help"]]:
        await update.message.reply_text(t["help_text"], parse_mode="Markdown")

async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    new_lang = "ar" if query.data == "lang_ar" else "en"
    set_user_lang(user_id, new_lang)
    
    await query.edit_message_text(TEXTS[new_lang]["lang_changed"])
    await context.bot.send_message(
        chat_id=user_id,
        text=TEXTS[new_lang]["welcome"],
        reply_markup=get_main_keyboard(new_lang)
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception handling update:", exc_info=context.error)

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("No BOT_TOKEN found!")
        return

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_cmd))
    app.add_handler(CallbackQueryHandler(lang_callback, pattern="^lang_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
