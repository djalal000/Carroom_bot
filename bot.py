import os
import logging
from dotenv import load_dotenv
from telegram import (
    Update, ReplyKeyboardMarkup, ReplyKeyboardRemove,
    InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackQueryHandler
)
from database import init_db, add_car, get_cars_under_price, get_car_by_id

# Load environment variables
load_dotenv()

# Configuration from .env
BOT_TOKEN = os.getenv('BOT_TOKEN')
IMAGES_DIR = os.getenv('IMAGES_DIR', 'car_images')

# Validate required environment variables
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file. Please add it.")

# Conversation states
MODEL, YEAR, PRICE, PHONE, IMAGE = range(5)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure image directory exists
os.makedirs(IMAGES_DIR, exist_ok=True)


# ----------- Helper Menu Buttons -------------
def main_menu_keyboard():
    """Persistent main menu with clear icons"""
    return ReplyKeyboardMarkup(
        [
            ["🚗 أضف سيارة", "🔍 تصفح السيارات"],
            ["📊 إحصائيات", "ℹ️ مساعدة"]
        ],
        resize_keyboard=True,
        is_persistent=True
    )


def cancel_keyboard():
    """Cancel button during operations"""
    return ReplyKeyboardMarkup(
        [["❌ إلغاء", "🏠 القائمة الرئيسية"]],
        resize_keyboard=True,
        one_time_keyboard=False
    )


def explore_keyboard():
    """Filter menu for browsing cars"""
    return ReplyKeyboardMarkup(
        [
            ["💵 أقل من 50M", "💰 أقل من 100M"],
            ["💎 أقل من 200M", "📋 كل السيارات"],
            ["🏠 القائمة الرئيسية"]
        ],
        resize_keyboard=True
    )


# ----------- Bot Commands Setup -------------
async def post_init(application: Application):
    """Set bot commands menu"""
    commands = [
        BotCommand("start", "🏠 القائمة الرئيسية"),
        BotCommand("addcar", "🚗 إضافة سيارة جديدة"),
        BotCommand("explore", "🔍 تصفح السيارات"),
        BotCommand("stats", "📊 إحصائيات السوق"),
        BotCommand("help", "ℹ️ المساعدة والدعم"),
        BotCommand("cancel", "❌ إلغاء العملية الحالية")
    ]
    await application.bot.set_my_commands(commands)


# ----------- Start & Help -------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message with main menu"""
    welcome_msg = (
        "🎉 *مرحباً بك في سوق السيارات!*\n\n"
        "🚗 منصتك المثالية لشراء وبيع السيارات\n\n"
        "*ماذا تريد أن تفعل؟*\n"
        "• 🚗 *أضف سيارة* - لعرض سيارتك للبيع\n"
        "• 🔍 *تصفح السيارات* - للبحث عن سيارة مناسبة\n"
        "• 📊 *إحصائيات* - معلومات عن السوق\n"
        "• ℹ️ *مساعدة* - دليل الاستخدام\n\n"
        "💡 *نصيحة:* يمكنك الوصول للأوامر من القائمة أسفل الشاشة أو من زر القائمة بجانب حقل الكتابة 📝"
    )
    await update.message.reply_text(
        welcome_msg,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help and instructions"""
    help_text = (
        "📖 *دليل استخدام البوت*\n\n"
        "*🚗 لإضافة سيارة:*\n"
        "1️⃣ اضغط على 'أضف سيارة'\n"
        "2️⃣ أدخل معلومات السيارة خطوة بخطوة\n"
        "3️⃣ أرسل صورة واضحة للسيارة\n\n"
        "*🔍 للبحث عن سيارة:*\n"
        "1️⃣ اضغط على 'تصفح السيارات'\n"
        "2️⃣ اختر نطاق السعر المناسب\n"
        "3️⃣ تصفح النتائج واتصل بالبائع\n\n"
        "*💡 نصائح مهمة:*\n"
        "• استخدم القائمة الدائمة أسفل الشاشة\n"
        "• يمكنك إلغاء أي عملية بالضغط على 'إلغاء'\n"
        "• الأسعار بالمليون دينار جزائري\n\n"
        "*🆘 بحاجة لمساعدة؟*\n"
        "تواصل مع: @support_username"
    )
    await update.message.reply_text(
        help_text,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show marketplace statistics"""
    all_cars = get_cars_under_price(10**9, limit=1000)
    total = len(all_cars)
    
    under_50 = len([c for c in all_cars if c[5] < 50])
    under_100 = len([c for c in all_cars if c[5] < 100])
    under_200 = len([c for c in all_cars if c[5] < 200])
    
    stats_text = (
        "📊 *إحصائيات سوق السيارات*\n\n"
        f"🚗 إجمالي السيارات: *{total}*\n\n"
        "*توزيع الأسعار:*\n"
        f"💵 أقل من 50M: {under_50} سيارة\n"
        f"💰 أقل من 100M: {under_100} سيارة\n"
        f"💎 أقل من 200M: {under_200} سيارة\n\n"
        "📈 السوق نشط ومتجدد يومياً!"
    )
    await update.message.reply_text(
        stats_text,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )


# ----------- Add Car Flow -------------
async def addcar_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start adding car process"""
    await update.message.reply_text(
        "🚘 *خطوة 1 من 5*\n\n"
        "أدخل موديل السيارة:\n"
        "مثال: `Toyota Corolla` أو `Hyundai Elantra`",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    return MODEL


async def addcar_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if text in ["❌ إلغاء", "🏠 القائمة الرئيسية"]:
        return await cancel(update, context)

    context.user_data['model'] = text
    await update.message.reply_text(
        "📅 *خطوة 2 من 5*\n\n"
        "أدخل سنة الصنع:\n"
        "مثال: `2020` أو `2018`",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    return YEAR


async def addcar_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if text in ["❌ إلغاء", "🏠 القائمة الرئيسية"]:
        return await cancel(update, context)

    if not text.isdigit() or len(text) != 4:
        await update.message.reply_text(
            "⚠️ يرجى إدخال سنة صحيحة (4 أرقام)\n"
            "مثال: `2020`",
            reply_markup=cancel_keyboard(),
            parse_mode="Markdown"
        )
        return YEAR

    year = int(text)
    if year < 1990 or year > 2025:
        await update.message.reply_text(
            "⚠️ السنة يجب أن تكون بين 1990 و 2025",
            reply_markup=cancel_keyboard()
        )
        return YEAR

    context.user_data['year'] = year
    await update.message.reply_text(
        "💰 *خطوة 3 من 5*\n\n"
        "أدخل السعر بالمليون دينار:\n"
        "مثال: `45` (يعني 45 مليون)",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    return PRICE


async def addcar_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if text in ["❌ إلغاء", "🏠 القائمة الرئيسية"]:
        return await cancel(update, context)

    try:
        price = int(text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "⚠️ يرجى إدخال رقم صحيح للسعر\n"
            "مثال: `45` أو `120`",
            reply_markup=cancel_keyboard(),
            parse_mode="Markdown"
        )
        return PRICE

    context.user_data['price'] = price
    await update.message.reply_text(
        "📞 *خطوة 4 من 5*\n\n"
        "أدخل رقم الهاتف:\n"
        "مثال: `+213555123456` أو `0555123456`",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    return PHONE


async def addcar_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if text in ["❌ إلغاء", "🏠 القائمة الرئيسية"]:
        return await cancel(update, context)

    context.user_data['phone'] = text
    await update.message.reply_text(
        "📸 *خطوة 5 من 5 (الأخيرة)*\n\n"
        "أرسل صورة واضحة للسيارة:\n"
        "• الصورة يجب أن تكون واضحة\n"
        "• يفضل صورة من الخارج\n"
        "• تجنب الصور المشوشة",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    return IMAGE


async def addcar_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text(
            "⚠️ لم أستلم صورة!\n"
            "يرجى إرسال صورة واحدة من فضلك 📸"
        )
        return IMAGE

    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_path = os.path.join(IMAGES_DIR, f"{photo.file_id}.jpg")
    await file.download_to_drive(file_path)

    data = context.user_data
    user = update.message.from_user
    username = user.username or f"{user.first_name or ''} {user.last_name or ''}".strip()
    
    car_id = add_car(
        user.id, username, data['model'], data['year'],
        data['price'], data['phone'], file_path
    )

    context.user_data.clear()
    
    success_msg = (
        "✅ *تم نشر إعلانك بنجاح!*\n\n"
        f"🆔 رقم الإعلان: `{car_id}`\n"
        f"🚘 الموديل: {data['model']}\n"
        f"📅 السنة: {data['year']}\n"
        f"💰 السعر: {data['price']}M\n\n"
        "🎉 إعلانك الآن ظاهر للجميع!\n"
        "📱 سيتواصل معك المشترون قريباً"
    )
    
    await update.message.reply_text(
        success_msg,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


# ----------- Cancel -------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ تم إلغاء العملية\n\n"
        "🏠 عدت إلى القائمة الرئيسية",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END


# ----------- Explore -------------
async def explore_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start browsing cars"""
    await update.message.reply_text(
        "🔍 *تصفح السيارات المتاحة*\n\n"
        "اختر نطاق السعر المناسب لك:\n"
        "💵 أقل من 50M\n"
        "💰 أقل من 100M\n"
        "💎 أقل من 200M\n"
        "📋 كل السيارات المتاحة",
        reply_markup=explore_keyboard(),
        parse_mode="Markdown"
    )


async def filter_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle filter selection"""
    text = update.message.text
    
    if "القائمة الرئيسية" in text:
        await start(update, context)
        return

    # Determine price filter
    if "50" in text:
        maxp = 50
        filter_name = "أقل من 50 مليون"
    elif "100" in text:
        maxp = 100
        filter_name = "أقل من 100 مليون"
    elif "200" in text:
        maxp = 200
        filter_name = "أقل من 200 مليون"
    else:
        maxp = 10**9
        filter_name = "كل السيارات"

    cars = get_cars_under_price(maxp, limit=30)
    
    if not cars:
        await update.message.reply_text(
            f"🚫 *لا توجد سيارات متاحة*\n\n"
            f"الفلتر: {filter_name}\n"
            f"جرب فلتر آخر أو أضف سيارتك للبيع! 🚗",
            reply_markup=explore_keyboard(),
            parse_mode="Markdown"
        )
        return

    # Send header message
    await update.message.reply_text(
        f"🔍 *نتائج البحث: {filter_name}*\n"
        f"📊 عدد النتائج: {len(cars)} سيارة\n\n"
        f"⬇️ جاري عرض السيارات...",
        parse_mode="Markdown"
    )

    # Send each car
    for car in cars:
        car_id, user_id, username, model, year, price, phone, image_path, created_at = car
        
        caption = (
            f"🆔 الإعلان رقم: `{car_id}`\n\n"
            f"🚘 *{model}*\n"
            f"📅 السنة: {year}\n"
            f"💰 السعر: {price} مليون \n"
            f"📞 الهاتف: `{phone}`\n"
            f"🕐 النشر: {created_at}\n\n"
            f"💡 انسخ رقم الهاتف أعلاه واتصل مباشرة"
        )
        
        buttons = [
            [InlineKeyboardButton("📞 انسخ رقم الهاتف", callback_data=f"COPY_{car_id}_{phone}")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as img:
                await update.message.reply_photo(
                    photo=img,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
        else:
            await update.message.reply_text(
                caption,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

    # Send footer with navigation
    await update.message.reply_text(
        "✅ *انتهى عرض النتائج*\n\n"
        "اختر سيارة أخرى أو عد للقائمة الرئيسية 🏠",
        reply_markup=explore_keyboard(),
        parse_mode="Markdown"
    )


# ----------- Detail View -------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button clicks"""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("COPY_"):
        # Extract phone number from callback data
        parts = data.split("_", 2)
        if len(parts) >= 3:
            phone = parts[2]
            await query.answer(
                f"📞 رقم الهاتف: {phone}\nانسخه واتصل الآن!",
                show_alert=True
            )
        return

    if data.startswith("DETAIL_"):
        car_id = int(data.split("_", 1)[1])
        car = get_car_by_id(car_id)
        
        if not car:
            await query.edit_message_caption(
                caption="🚫 *عذراً، هذا الإعلان لم يعد متاحاً*",
                parse_mode="Markdown"
            )
            return

        _, user_id, username, model, year, price, phone, image_path, created_at = car
        
        detail_text = (
            f"📋 *معلومات الإعلان الكاملة*\n"
            f"{'='*30}\n\n"
            f"🆔 رقم الإعلان: `{car_id}`\n\n"
            f"🚗 *تفاصيل السيارة:*\n"
            f"   • الموديل: *{model}*\n"
            f"   • سنة الصنع: {year}\n"
            f"   • السعر: {price} مليون دينار جزائري\n\n"
            f"👤 *معلومات البائع:*\n"
            f"   • الاسم: @{username if username else 'مستخدم'}\n"
            f"   • رقم الهاتف: `{phone}`\n\n"
            f"📅 *تاريخ النشر:* {created_at}\n\n"
            f"{'='*30}\n"
            f"📞 *للاتصال:* اضغط على رقم الهاتف أعلاه للنسخ،\n"
            f"ثم اتصل مباشرة بالبائع عبر الهاتف\n\n"
            f"أو أرسل رسالة للبائع عبر تيليجرام 👇"
        )
        
        buttons = [
            [InlineKeyboardButton("✉️ مراسلة البائع عبر تيليجرام", url=f"tg://user?id={user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)

        await query.message.reply_text(
            detail_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )


# ----------- Main Menu Handler -------------
async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu button presses"""
    text = update.message.text
    
    if "أضف سيارة" in text:
        await addcar_start(update, context)
    elif "تصفح السيارات" in text:
        await explore_start(update, context)
    elif "إحصائيات" in text:
        await stats_command(update, context)
    elif "مساعدة" in text:
        await help_command(update, context)


# ----------- Main -------------
def main():
    """Initialize and start the bot"""
    init_db()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Conversation handler for adding cars
    conv = ConversationHandler(
        entry_points=[
            CommandHandler('addcar', addcar_start),
            MessageHandler(filters.Regex("🚗 أضف سيارة"), addcar_start)
        ],
        states={
            MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, addcar_model)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, addcar_year)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, addcar_price)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, addcar_phone)],
            IMAGE: [MessageHandler(filters.PHOTO, addcar_image)],
        },
        fallbacks=[
            MessageHandler(filters.Regex("❌ إلغاء|🏠 القائمة الرئيسية"), cancel),
            CommandHandler('cancel', cancel)
        ]
    )

    # Command handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('stats', stats_command))
    app.add_handler(CommandHandler('explore', explore_start))
    app.add_handler(CommandHandler('cancel', cancel))
    
    # Conversation handler
    app.add_handler(conv)
    
    # Menu handlers
    app.add_handler(MessageHandler(filters.Regex("🔍 تصفح السيارات"), explore_start))
    app.add_handler(MessageHandler(filters.Regex("📊 إحصائيات"), stats_command))
    app.add_handler(MessageHandler(filters.Regex("ℹ️ مساعدة"), help_command))
    app.add_handler(MessageHandler(
        filters.Regex(r'أقل من|كل السيارات|القائمة الرئيسية'),
        filter_choice
    ))
    
    # Callback query handler
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🚀 Car Market Bot started successfully!")
    app.run_polling()


if __name__ == "__main__":
    main()