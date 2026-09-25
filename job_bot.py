from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# تخزين بيانات المستخدمين في الذاكرة (يفضل مستقبلاً استخدام قاعدة بيانات)
user_data = {}

# قائمة الدول الشائعة للعمل أونلاين
POPULAR_COUNTRIES = ["مصر", "السعودية", "الإمارات", "أمريكا", "ألمانيا", "الكل"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = user_data.get(user_id, {"skills": [], "experience": "", "education": "", "countries": []})
    
    keyboard = [
        [InlineKeyboardButton("🎓 تحديد التعليم", callback_data="set_education")],
        [InlineKeyboardButton("⭐ تحديد مستوى الخبرة", callback_data="set_experience")],
        [InlineKeyboardButton("🛠️ إضافة مهارة", callback_data="add_skill")],
        [InlineKeyboardButton("🌍 تحديد دول العمل", callback_data="set_country")],
        [InlineKeyboardButton("🔍 البحث عن دولة محددة", callback_data="search_country")],
        [InlineKeyboardButton("📋 عرض الملف الشخصي", callback_data="show_profile")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("مرحباً بك! اختر القائمة التي تريد ضبطها للعمل أونلاين:", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "set_education":
        keyboard = [
            [InlineKeyboardButton("ثانوية عامة", callback_data="edu_High School")],
            [InlineKeyboardButton("بكالوريوس / ليثانس", callback_data="edu_Bachelor")],
            [InlineKeyboardButton("ماجستير / دكتوراه", callback_data="edu_Master_PhD")]
        ]
        await query.edit_message_text("اختر مستواك التعليمي:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("edu_"):
        edu = data.split("_")[1]
        user_data[user_id]["education"] = edu
        await query.edit_message_text(f"تم حفظ التعليم: {edu}")

    elif data == "set_experience":
        keyboard = [
            [InlineKeyboardButton("مبتدئ (Junior)", callback_data="exp_Junior")],
            [InlineKeyboardButton("متوسط (Mid-Level)", callback_data="exp_Mid-Level")],
            [InlineKeyboardButton("خبير (Senior)", callback_data="exp_Senior")]
        ]
        await query.edit_message_text("اختر مستوى خبرتك:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("exp_"):
        exp = data.split("_")[1]
        user_data[user_id]["experience"] = exp
        await query.edit_message_text(f"تم حفظ مستوى الخبرة: {exp}")

    elif data == "add_skill":
        context.user_data["awaiting_input"] = "skill"
        await query.edit_message_text("اكتب المهارة التي تريد إضافتها في الشات الآن (مثال: Python, Graphic Design):")

    elif data == "set_country":
        keyboard = [[InlineKeyboardButton(country, callback_data=f"country_{country}")] for country in POPULAR_COUNTRIES]
        await query.edit_message_text("اختر دولة من القائمة للعمل منها أونلاين:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("country_"):
        country = data.split("_")[1]
        if country not in user_data[user_id]["countries"]:
            user_data[user_id]["countries"].append(country)
        await query.edit_message_text(f"تمت إضافة {country} إلى قائمة الدول المفضلة.")

    elif data == "search_country":
        context.user_data["awaiting_input"] = "search_country"
        await query.edit_message_text("اكتب اسم الدولة التي تريد البحث عنها وإضافتها في الشات الآن:")

    elif data == "show_profile":
        info = user_data.get(user_id, {})
        skills = ", ".join(info.get("skills", [])) or "لم تحدد"
        countries = ", ".join(info.get("countries", [])) or "لم تحدد"
        text = (
            f"👤 **بياناتك للعمل أونلاين:**\n\n"
            f"🎓 التعليم: {info.get('education', 'غير محدد')}\n"
            f"⭐ الخبرة: {info.get('experience', 'غير محدد')}\n"
            f"🛠️ المهارات: {skills}\n"
            f"🌍 الدول المختارة: {countries}"
        )
        await query.edit_message_text(text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = context.user_data.get("awaiting_input")
    text = update.message.text.strip()

    if state == "skill":
        user_data[user_id]["skills"].append(text)
        context.user_data["awaiting_input"] = None
        await update.message.reply_text(f"✅ تمت إضافة المهارة: {text}")

    elif state == "search_country":
        if text not in user_data[user_id]["countries"]:
            user_data[user_id]["countries"].append(text)
        context.user_data["awaiting_input"] = None
        await update.message.reply_text(f"✅ تم العثور على الدولة وإضافتها: {text}")

if __name__ == "__main__"8887237109:AAEFRaH5SUwgGbOytQW456ynnlz3uQ3hJKY"

    app = ApplicationBuilder().token("8887237109:AAEvWP5C_Xou9UluRoJgkfBMrGjoJBD9ExA").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()
