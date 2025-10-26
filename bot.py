# bot.py
import os
import logging
from dotenv import load_dotenv
from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackQueryHandler
)
from database import init_db, add_car, get_cars_under_price, get_car_by_id, get_user_cars, delete_car, get_user_language, set_user_language
from languages import LANGS

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
IMAGES_DIR = os.getenv('IMAGES_DIR', 'car_images')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file. Please add it.")

# Conversation states
MODEL, YEAR, PRICE, MILES, LOCATION, CONDITION, PHONE, IMAGE = range(8)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure directories
os.makedirs(IMAGES_DIR, exist_ok=True)

# Translation helper
def t(user_id, key, **kwargs):
    lang = get_user_language(user_id)
    text = LANGS.get(lang, LANGS['en']).get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

# Localized main menu
def main_menu_keyboard(user_id):
    lang = get_user_language(user_id)
    return ReplyKeyboardMarkup(
        LANGS.get(lang, LANGS['en'])['main_menu'],
        resize_keyboard=True,
        is_persistent=True
    )

# Localized cancel keyboard
def cancel_keyboard(user_id):
    lang = get_user_language(user_id)
    return ReplyKeyboardMarkup(
        LANGS.get(lang, LANGS['en'])['cancel_menu'],
        resize_keyboard=True,
        one_time_keyboard=False
    )

# Localized explore keyboard
def explore_keyboard(user_id):
    lang = get_user_language(user_id)
    return ReplyKeyboardMarkup(
        LANGS.get(lang, LANGS['en'])['explore_menu'],
        resize_keyboard=True
    )

# Language selection keyboard
def language_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇺🇸 English", callback_data="LANG_en"),
            InlineKeyboardButton("🇫🇷 Français", callback_data="LANG_fr")
        ],
        [
            InlineKeyboardButton("🇸🇦 العربية", callback_data="LANG_ar")
        ]
    ])

# Format car caption with robust type handling
def format_car_caption(car, user_id, is_my_car=False):
    # Handle both tuple and Row objects from SQLite
    if hasattr(car, 'keys'):  # sqlite3.Row object
        car_id = car['id']
        username = car['username']
        model = car['model']
        year = car['year']
        price = car['price']
        miles = car['miles']
        location = car['location']
        condition = car['condition']
        phone = car['phone']
        image_path = car['image_path']
        created_at = car['created_at']
    else:  # Tuple
        car_id, _, username, model, year, price, miles, location, condition, phone, image_path, created_at = car
    
    keys = LANGS[get_user_language(user_id)]
    
    # Convert to integers to ensure proper formatting
    try:
        year = int(year)
        price = int(price)
        miles = int(miles)
        condition = int(condition)
    except (ValueError, TypeError) as e:
        # Log the error for debugging
        print(f"Type conversion error: {e}, types: year={type(year)}, price={type(price)}, miles={type(miles)}")
    
    caption = (
        f"<b>🚘 {model}</b>\n"
        f"<b>{keys['year_label']}</b> {year}\n"
        f"<b>{keys['price_label']}</b> ${price:,.0f}\n"
        f"<b>{keys['miles_label']}</b> {miles:,}\n"
        f"<b>{keys['location_label']}</b> {location}\n"
        f"<b>{keys['condition_label']}</b> {condition}/10\n"
        f"<b>{keys['phone_label']}</b> <code>{phone}</code>\n"
        f"<b>{keys['posted_label']}</b> {created_at}\n\n"
        f"{keys['manage_tip'] if is_my_car else keys['contact_tip']}"
    )
    return caption

# Bot commands setup
async def post_init(application: Application):
    commands = [
        BotCommand("start", "🏠 Main Menu"),
        BotCommand("addcar", "🚗 Add New Car"),
        BotCommand("explore", "🔍 Browse Cars"),
        BotCommand("mycars", "🗂️ Manage My Cars"),
        BotCommand("stats", "📊 Market Stats"),
        BotCommand("help", "ℹ️ Help and Support"),
        BotCommand("lang", "🌐 Change Language"),
        BotCommand("cancel", "❌ Cancel Current Operation")
    ]
    await application.bot.set_my_commands(commands)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await update.message.reply_text(
        t(user_id, 'welcome'),
        reply_markup=main_menu_keyboard(user_id),
        parse_mode="HTML"
    )

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await update.message.reply_text(
        t(user_id, 'help'),
        reply_markup=main_menu_keyboard(user_id),
        parse_mode="HTML"
    )

# Stats command
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    all_cars = get_cars_under_price(1000000, limit=1000)
    total = len(all_cars)
    under_10k = len([c for c in all_cars if c[5] < 10000])
    under_20k = len([c for c in all_cars if c[5] < 20000])
    under_30k = len([c for c in all_cars if c[5] < 30000])
    await update.message.reply_text(
        t(user_id, 'stats', total=total, under_10k=under_10k, under_20k=under_20k, under_30k=under_30k),
        reply_markup=main_menu_keyboard(user_id),
        parse_mode="HTML"
    )

# Language menu
async def language_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await update.message.reply_text(
        t(user_id, 'choose_language'),
        reply_markup=language_keyboard(),
        parse_mode="HTML"
    )

# Add car flow
async def addcar_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await update.message.reply_text(
        t(user_id, 'add_step1'),
        reply_markup=cancel_keyboard(user_id),
        parse_mode="HTML"
    )
    return MODEL

async def addcar_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.startswith("❌") or text.startswith("🏠"):
        return await cancel(update, context)
    context.user_data['model'] = text
    user_id = update.message.from_user.id
    await update.message.reply_text(
        t(user_id, 'add_step2'),
        reply_markup=cancel_keyboard(user_id),
        parse_mode="HTML"
    )
    return YEAR

async def addcar_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.message.from_user.id
    if text.startswith("❌") or text.startswith("🏠"):
        return await cancel(update, context)
    if not text.isdigit() or len(text) != 4:
        await update.message.reply_text(
            t(user_id, 'add_step2_invalid_format'),
            reply_markup=cancel_keyboard(user_id),
            parse_mode="HTML"
        )
        return YEAR
    year = int(text)
    if year < 1990 or year > 2025:
        await update.message.reply_text(
            t(user_id, 'add_step2_invalid_range'),
            reply_markup=cancel_keyboard(user_id),
            parse_mode="HTML"
        )
        return YEAR
    context.user_data['year'] = year
    await update.message.reply_text(
        t(user_id, 'add_step3'),
        reply_markup=cancel_keyboard(user_id),
        parse_mode="HTML"
    )
    return PRICE

async def addcar_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.message.from_user.id
    if text.startswith("❌") or text.startswith("🏠"):
        return await cancel(update, context)
    try:
        price = int(text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            t(user_id, 'add_step3_invalid'),
            reply_markup=cancel_keyboard(user_id),
            parse_mode="HTML"
        )
        return PRICE
    context.user_data['price'] = price
    await update.message.reply_text(
        t(user_id, 'add_step4'),
        reply_markup=cancel_keyboard(user_id),
        parse_mode="HTML"
    )
    return MILES

async def addcar_miles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.message.from_user.id
    if text.startswith("❌") or text.startswith("🏠"):
        return await cancel(update, context)
    try:
        miles = int(text)
        if miles < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            t(user_id, 'add_step4_invalid'),
            reply_markup=cancel_keyboard(user_id),
            parse_mode="HTML"
        )
        return MILES
    context.user_data['miles'] = miles
    await update.message.reply_text(
        t(user_id, 'add_step5'),
        reply_markup=cancel_keyboard(user_id),
        parse_mode="HTML"
    )
    return LOCATION

async def addcar_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.message.from_user.id
    if text.startswith("❌") or text.startswith("🏠"):
        return await cancel(update, context)
    context.user_data['location'] = text
    await update.message.reply_text(
        t(user_id, 'add_step6'),
        reply_markup=cancel_keyboard(user_id),
        parse_mode="HTML"
    )
    return CONDITION

async def addcar_condition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.message.from_user.id
    if text.startswith("❌") or text.startswith("🏠"):
        return await cancel(update, context)
    try:
        condition = int(text)
        if not 1 <= condition <= 10:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            t(user_id, 'add_step6_invalid'),
            reply_markup=cancel_keyboard(user_id),
            parse_mode="HTML"
        )
        return CONDITION
    context.user_data['condition'] = condition
    await update.message.reply_text(
        t(user_id, 'add_step7'),
        reply_markup=cancel_keyboard(user_id),
        parse_mode="HTML"
    )
    return PHONE

async def addcar_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.message.from_user.id
    if text.startswith("❌") or text.startswith("🏠"):
        return await cancel(update, context)
    digits = ''.join(filter(lambda x: x.isdigit() or x == '+', text))
    context.user_data['phone'] = digits
    await update.message.reply_text(
        t(user_id, 'add_step8'),
        reply_markup=cancel_keyboard(user_id),
        parse_mode="HTML"
    )
    return IMAGE

async def addcar_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not update.message.photo:
        await update.message.reply_text(
            t(user_id, 'add_image_invalid'),
            parse_mode="HTML"
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
        data['price'], data['miles'], data['location'],
        data['condition'], data['phone'], file_path
    )
    context.user_data.clear()
    await update.message.reply_text(
        t(user_id, 'add_success', car_id=car_id, model=data['model'], year=data['year'], price=data['price'], miles=data['miles'], location=data['location'], condition=data['condition'], phone=data['phone']),
        reply_markup=main_menu_keyboard(user_id),
        parse_mode="HTML"
    )
    return ConversationHandler.END

# Cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    context.user_data.clear()
    await update.message.reply_text(
        t(user_id, 'cancelled'),
        reply_markup=main_menu_keyboard(user_id),
        parse_mode="HTML"
    )
    return ConversationHandler.END

# Explore start
async def explore_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await update.message.reply_text(
        t(user_id, 'explore'),
        reply_markup=explore_keyboard(user_id),
        parse_mode="HTML"
    )

# Filter choice
async def filter_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id
    if text.startswith("🏠"):
        await start(update, context)
        return
    if "10K" in text:
        maxp = 10000
        filter_name = t(user_id, 'under_10k')
    elif "20K" in text:
        maxp = 20000
        filter_name = t(user_id, 'under_20k')
    elif "30K" in text:
        maxp = 30000
        filter_name = t(user_id, 'under_30k')
    else:
        maxp = 1000000
        filter_name = t(user_id, 'all_cars')
    cars = get_cars_under_price(maxp, limit=30)
    if not cars:
        await update.message.reply_text(
            t(user_id, 'no_cars', filter_name=filter_name),
            reply_markup=explore_keyboard(user_id),
            parse_mode="HTML"
        )
        return
    await update.message.reply_text(
        t(user_id, 'results_header', filter_name=filter_name, count=len(cars)),
        parse_mode="HTML"
    )
    for car in cars:
        caption = format_car_caption(car, user_id)
        buttons = [
            [
                InlineKeyboardButton(t(user_id, 'copy_phone'), callback_data=f"COPY_{car[0]}_{car[9]}"),
                InlineKeyboardButton(t(user_id, 'message_seller'), url=f"tg://user?id={car[1]}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        image_path = car[10]
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as img:
                await update.message.reply_photo(
                    photo=img,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
        else:
            await update.message.reply_text(
                caption,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    await update.message.reply_text(
        t(user_id, 'end_results'),
        reply_markup=explore_keyboard(user_id),
        parse_mode="HTML"
    )

# My cars
async def my_cars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cars = get_user_cars(user_id)
    if not cars:
        await update.message.reply_text(
            t(user_id, 'no_listings'),
            reply_markup=main_menu_keyboard(user_id),
            parse_mode="HTML"
        )
        return
    await update.message.reply_text(
        t(user_id, 'my_cars_header', count=len(cars)),
        parse_mode="HTML"
    )
    for car in cars:
        caption = format_car_caption(car, user_id, is_my_car=True)
        buttons = [
            [
                InlineKeyboardButton(t(user_id, 'delete'), callback_data=f"CONFIRM_{car[0]}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        image_path = car[10]
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as img:
                await update.message.reply_photo(
                    photo=img,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
        else:
            await update.message.reply_text(
                caption,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    await update.message.reply_text(
        t(user_id, 'my_cars_end'),
        reply_markup=main_menu_keyboard(user_id),
        parse_mode="HTML"
    )

# Button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    if data.startswith("LANG_"):
        lang = data.split("_")[1]
        set_user_language(user_id, lang)
        await query.edit_message_text(
            t(user_id, 'language_changed', lang=lang.upper()),
            parse_mode="HTML"
        )
        await query.message.reply_text(
            t(user_id, 'welcome'),
            reply_markup=main_menu_keyboard(user_id),
            parse_mode="HTML"
        )
        return
    if data.startswith("COPY_"):
        parts = data.split("_", 2)
        if len(parts) >= 3:
            phone = parts[2]
            await query.answer(
                t(user_id, 'phone_copied', phone=phone),
                show_alert=True
            )
        return
    if data.startswith("CONFIRM_"):
        car_id = int(data.split("_")[1])
        new_buttons = [
            [
                InlineKeyboardButton(t(user_id, 'yes_delete'), callback_data=f"YES_DELETE_{car_id}"),
                InlineKeyboardButton(t(user_id, 'no_delete'), callback_data="NO_DELETE")
            ]
        ]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(new_buttons))
        return
    if data == "NO_DELETE":
        await query.edit_message_reply_markup(reply_markup=None)
        await query.answer(t(user_id, 'deletion_cancelled'))
        return
    if data.startswith("YES_DELETE_"):
        car_id = int(data.split("_")[2])
        deleted = delete_car(car_id, user_id)
        if deleted:
            await query.edit_message_caption(
                caption=t(user_id, 'listing_deleted_caption'),
                parse_mode="HTML"
            )
            await query.answer(t(user_id, 'listing_deleted'))
        else:
            await query.answer(t(user_id, 'delete_failed'), show_alert=True)
        return

# Main menu handler
async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.startswith("🚗"):
        await addcar_start(update, context)
    elif text.startswith("🔍"):
        await explore_start(update, context)
    elif text.startswith("🗂️"):
        await my_cars(update, context)
    elif text.startswith("📊"):
        await stats_command(update, context)
    elif text.startswith("ℹ️"):
        await help_command(update, context)
    elif text.startswith("🌐"):
        await language_menu(update, context)

# Main function
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler('addcar', addcar_start),
            MessageHandler(filters.Regex(r"^🚗"), addcar_start)
        ],
        states={
            MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, addcar_model)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, addcar_year)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, addcar_price)],
            MILES: [MessageHandler(filters.TEXT & ~filters.COMMAND, addcar_miles)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, addcar_location)],
            CONDITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, addcar_condition)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, addcar_phone)],
            IMAGE: [MessageHandler(filters.PHOTO, addcar_image)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            MessageHandler(filters.Regex(r"^❌|^🏠"), cancel)
        ]
    )

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('stats', stats_command))
    app.add_handler(CommandHandler('explore', explore_start))
    app.add_handler(CommandHandler('mycars', my_cars))
    app.add_handler(CommandHandler('lang', language_menu))
    app.add_handler(CommandHandler('cancel', cancel))

    app.add_handler(conv)

    app.add_handler(MessageHandler(filters.Regex(r"^🔍"), explore_start))
    app.add_handler(MessageHandler(filters.Regex(r"^🗂️"), my_cars))
    app.add_handler(MessageHandler(filters.Regex(r"^📊"), stats_command))
    app.add_handler(MessageHandler(filters.Regex(r"^ℹ️"), help_command))
    app.add_handler(MessageHandler(filters.Regex(r"^🌐"), language_menu))
    app.add_handler(MessageHandler(filters.Regex(r"Under|أقل من|Moins de|All Cars|جميع|Toutes les|Main Menu|القائمة|Menu"), filter_choice))

    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🚀 Car Marketplace Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()