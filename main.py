import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import time
import logging
import uuid
from datetime import datetime

# شناسه ادمین
ADMIN_ID = 99510185

# این خط‌ها برای راه‌اندازی سرور Flask و گرفتن URL عمومی
from background import keep_alive
keep_alive()

# تنظیم لاگ برای دیباگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# توکن ربات
TOKEN = "8130794230:AAHWF5jJ4mndYc1W8t2g_YIBbEGwjnV8sd4"
bot = telebot.TeleBot(TOKEN)

# دیکشنری‌ها برای ذخیره اطلاعات
pending_payments = {}  # برای ذخیره پرداخت‌های در انتظار تأیید
user_orders = {}  # ساختار: {chat_id: {item: count}}
user_counts = {}  # تعداد نفرات
user_entry_type = {}  # نوع ورود (with_car یا without_car)

# قیمت‌ها (فقط برای محاسبه در پس‌زمینه)
prices = {
    "starter_olive": ("زیتون ساده", 40),
    "starter_olive_stuffed": ("زیتون پرورده", 50),
    "starter_yogurt": ("ماست و خیار", 50),
    "starter_pickle": ("شور", 30),
    "starter_cucumber_tomato": ("خیار و گوجه", 30),
    "main_kashk": ("کشک بادمجان", 150),
    "main_pasta": ("ماکارونی", 160),
    "main_badkobe": ("بادکوبه", 150),
    "cocktail_dough": ("کوکتل دوغ", 100),
    "cocktail_watermelon": ("کوکتل هندوانه", 100),
    "cocktail_mojito": ("کوکتل موهیتو", 100)
}

# هزینه‌ها
ENTRY_FEE_WITH_CAR = 50  # هزینه ورود با ماشین به ازای هر نفر
ENTRY_FEE_BASE = 100    # هزینه ورودی پایه به ازای هر نفر

# تنظیم منوی همیشگی (دستورات پایین سمت چپ)
def set_persistent_menu():
    commands = [
        BotCommand("start", "🔄 شروع مجدد"),
        BotCommand("menu", "📜 نمایش منو"),
        BotCommand("checkout", "💳 مشاهده فاکتور"),
        BotCommand("edit", "📝 ویرایش فاکتور"),
        BotCommand("event", "📅 تاریخ جشن"),
        BotCommand("cocktail", "🍹 کوکتل"),
    ]
    bot.set_my_commands(commands)

# دکمه "🔙 بازگشت به منو"
def back_to_menu():
    markup = InlineKeyboardMarkup()
    btn_back = InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")
    markup.add(btn_back)
    return markup

# تابع برای محاسبه و نمایش زمان باقی‌مونده به جشن
def show_event_timer(chat_id):
    event_time = datetime(2025, 3, 18, 19, 0)
    now = datetime.now()
    time_diff = event_time - now
    if time_diff.total_seconds() > 0:
        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        timer_message = f"⏳ {days} روز و {hours} ساعت و {minutes} دقیقه مونده به جشن چهارشنبه‌سوری!🎇✨"
    else:
        timer_message = "🎉 جشن چهارشنبه‌سوری شروع شده! خوش اومدی!"
    bot.send_message(chat_id, timer_message, reply_markup=back_to_menu())

# ایجاد منوی اصلی
def main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("👥 تعداد نفرات", callback_data="select_count")
    btn2 = InlineKeyboardButton("🍽 پیش‌غذا", callback_data="starter")
    btn3 = InlineKeyboardButton("🥘 غذای اصلی", callback_data="main_course")
    btn4 = InlineKeyboardButton("🍹 کوکتل", callback_data="cocktail")
    btn5 = InlineKeyboardButton("📝 ویرایش فاکتور", callback_data="edit_order")
    btn6 = InlineKeyboardButton("💳 پرداخت نهایی", callback_data="checkout")
    btn7 = InlineKeyboardButton("📅 تاریخ جشن", callback_data="show_event")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
    return markup

# وقتی کاربر /start بزنه
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_orders[chat_id] = {}
    user_counts[chat_id] = 0
    user_entry_type[chat_id] = None

    first_name = message.from_user.first_name if message.from_user.first_name else "دوست عزیز"
    welcome_caption = (
        f"سلام {first_name} جان 😍\n"
        "خیلی خوشحالیم که مارو انتخاب کردی 🎉\n\n"
        "امیدوارم یک شب خفن و باحال رو با ما تجربه کنی🤩\n"
        "با چند کلیک ساده سفارش بده و لذت ببر! 😋\n\n"
    )
    set_persistent_menu()
    event_time = datetime(2025, 3, 18, 19, 0)
    now = datetime.now()
    time_diff = event_time - now
    if time_diff.total_seconds() > 0:
        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        timer_message = f"⏳ {days} روز و {hours} ساعت و {minutes} دقیقه مونده به جشن چهارشنبه‌سوری!🎇✨"
    else:
        timer_message = "🎉 جشن چهارشنبه‌سوری شروع شده! خوش اومدی!"
    welcome_caption += "\n\n" + timer_message
    try:
        with open("welcome_image.jpg", "rb") as photo:
            bot.send_photo(chat_id, photo, caption=welcome_caption, reply_markup=main_menu())
    except FileNotFoundError:
        bot.send_message(chat_id, welcome_caption, reply_markup=main_menu())
        logging.warning("عکس welcome_image.jpg پیدا نشد!")

# نمایش منو با /menu
@bot.message_handler(commands=['menu'])
def show_menu(message):
    bot.send_message(message.chat.id, "📜 منوی اصلی:", reply_markup=main_menu())

# نمایش تاریخ جشن با /event
@bot.message_handler(commands=['event'])
def show_event(message):
    show_event_timer(message.chat.id)

# مشاهده فاکتور با /checkout
@bot.message_handler(commands=['checkout'])
def checkout_command(message):
    show_invoice(message.chat.id)

# ویرایش فاکتور با /edit
@bot.message_handler(commands=['edit'])
def edit_command(message):
    edit_order(message.chat.id)

# نمایش منوی کوکتل با /cocktail
@bot.message_handler(commands=['cocktail'])
def cocktail_command(message):
    bot.send_message(message.chat.id, "🍹 کوکتل‌ها:\n👇 یکی از گزینه‌های زیر رو انتخاب کن:", reply_markup=cocktail_menu())

# تابع محاسبه کل مبلغ
def calculate_total(chat_id):
    if chat_id not in user_orders or not user_orders[chat_id] or chat_id not in user_counts or user_counts[chat_id] <= 0:
        return 0, 0, 0
    # محاسبه هزینه سفارش‌ها فقط بر اساس تعداد آیتم‌ها (بدون ضرب در نفرات)
    base_total = sum(prices[item][1] * count for item, count in user_orders[chat_id].items())
    # لاگ برای دیباگ
    logging.info(f"chat_id: {chat_id}, user_orders: {user_orders[chat_id]}, user_counts: {user_counts[chat_id]}")
    logging.info(f"base_total (items only): {base_total}")
    # محاسبه هزینه ورود با ماشین و ورودی پایه بر اساس تعداد نفرات
    entry_fee_car = ENTRY_FEE_WITH_CAR * user_counts[chat_id]
    entry_fee_base = ENTRY_FEE_BASE * user_counts[chat_id]
    entry_fee = entry_fee_car + entry_fee_base
    total = base_total + entry_fee
    return base_total, entry_fee, total

# واکنش به دکمه‌ها
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    logging.info(f"دکمه زده شد: {call.data}")

    try:
        if call.data == "starter":
            bot.send_message(chat_id, "🍽 پیش‌غذاهای موجود:\n👇 یکی از گزینه‌های زیر رو انتخاب کن:", reply_markup=starter_menu())
        elif call.data == "main_course":
            bot.send_message(chat_id, "🥘 غذای اصلی:\n👇 یکی از گزینه‌های زیر رو انتخاب کن:", reply_markup=main_course_menu())
        elif call.data == "cocktail":
            bot.send_message(chat_id, "🍹 کوکتل‌ها:\n👇 یکی از گزینه‌های زیر رو انتخاب کن:", reply_markup=cocktail_menu())
        elif call.data == "checkout":
            show_invoice(chat_id)
        elif call.data == "select_count":
            bot.send_message(chat_id, "👥 تعداد نفرات را انتخاب کنید:", reply_markup=select_count_menu())
        elif call.data.startswith("count_"):
            update_count(call)
        elif call.data == "edit_order":
            edit_order(chat_id)
        elif call.data.startswith("remove_"):
            remove_item(call)
        elif call.data == "show_event":
            show_event_timer(chat_id)
        elif call.data == "with_car":
            user_entry_type[chat_id] = "with_car"
            show_final_invoice(chat_id, "با ماشین")
        elif call.data == "without_car":
            user_entry_type[chat_id] = "without_car"
            show_final_invoice(chat_id, "بدون ماشین")
        elif call.data.startswith("approve_") or call.data.startswith("reject_"):
            admin_id = call.message.chat.id
            if admin_id != ADMIN_ID:
                bot.answer_callback_query(call.id, "⛔ شما اجازه انجام این عملیات را ندارید.")
                return
            payment_id = call.data.split("_")[1]
            if payment_id not in pending_payments:
                bot.answer_callback_query(call.id, "⛔ اطلاعات پرداخت یافت نشد!")
                return
            payment_info = pending_payments.pop(payment_id)
            user_id = payment_info["user_id"]
            username = payment_info["username"]
            total = payment_info["total"]
            items_list = payment_info["items"]
            if call.data.startswith("approve_"):
                bot.send_message(user_id, "✅ ممنون ازت!😎 بررسی شد و واریزی شما تأیید شد. بزودی باهات تماس می‌گیریم.")
                bot.send_message(ADMIN_ID, f"✅ پرداخت کاربر {username} تأیید شد. سفارش در حال پردازش است.")
                bot.answer_callback_query(call.id, "✅ پرداخت تأیید شد!")
            else:
                bot.send_message(user_id, "❌ رسید شما بررسی شد. به احتمال زیاد هنوز پرداختی از درگاه ارسال نشده. با آیدی زیر تماس بگیرید:\n@Shabahang67")
                bot.send_message(ADMIN_ID, f"❌ پرداخت کاربر {username} رد شد.")
                bot.answer_callback_query(call.id, "❌ پرداخت رد شد!")
            bot.edit_message_reply_markup(ADMIN_ID, call.message.message_id, reply_markup=None)
        elif call.data == "back_to_menu":
            bot.edit_message_text("📜 منوی اصلی:", chat_id, call.message.id, reply_markup=main_menu())
        elif call.data.startswith("select_count_"):
            parts = call.data.split("_")
            if len(parts) >= 4 and parts[0] == "select" and parts[1] == "count":
                item = "_".join(parts[2:-1])
                count = int(parts[-1])
                add_to_order(chat_id, item, count)
                bot.send_message(chat_id, f"✅ {prices[item][0]} ({count} عدد) به سفارش شما اضافه شد.", reply_markup=back_to_menu())
        elif call.data in prices:
            bot.send_message(chat_id, f"👇 تعداد {prices[call.data][0]} رو مشخص کن:", reply_markup=select_item_count_menu(call.data))
    except Exception as e:
        logging.error(f"خطا در پردازش دکمه: {e}")
        bot.send_message(chat_id, "⚠️ یه مشکلی پیش اومد، لطفاً دوباره امتحان کن!")

# تغییر تعداد نفرات
def update_count(call):
    chat_id = call.message.chat.id
    count = int(call.data.split("_")[1])
    user_counts[chat_id] = count
    bot.edit_message_text(f"✅ تعداد نفرات تنظیم شد: {count} نفر", chat_id, call.message.id, reply_markup=back_to_menu())

# منوی انتخاب پیش‌غذا (با قیمت)
def starter_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton(f"زیتون ساده - {prices['starter_olive'][1]} تومان", callback_data="starter_olive")
    btn2 = InlineKeyboardButton(f"زیتون پرورده - {prices['starter_olive_stuffed'][1]} تومان", callback_data="starter_olive_stuffed")
    btn3 = InlineKeyboardButton(f"ماست و خیار - {prices['starter_yogurt'][1]} تومان", callback_data="starter_yogurt")
    btn4 = InlineKeyboardButton(f"شور - {prices['starter_pickle'][1]} تومان", callback_data="starter_pickle")
    btn5 = InlineKeyboardButton(f"خیار و گوجه - {prices['starter_cucumber_tomato'][1]} تومان", callback_data="starter_cucumber_tomato")
    btn_back = InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn_back)
    return markup

# منوی انتخاب غذای اصلی (با قیمت)
def main_course_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton(f"کشک بادمجان - {prices['main_kashk'][1]} تومان", callback_data="main_kashk")
    btn2 = InlineKeyboardButton(f"ماکارونی - {prices['main_pasta'][1]} تومان", callback_data="main_pasta")
    btn3 = InlineKeyboardButton(f"بادکوبه - {prices['main_badkobe'][1]} تومان", callback_data="main_badkobe")
    btn_back = InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")
    markup.add(btn1, btn2, btn3, btn_back)
    return markup

# منوی انتخاب کوکتل (با قیمت)
def cocktail_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton(f"کوکتل دوغ - {prices['cocktail_dough'][1]} تومان", callback_data="cocktail_dough")
    btn2 = InlineKeyboardButton(f"کوکتل هندوانه - {prices['cocktail_watermelon'][1]} تومان", callback_data="cocktail_watermelon")
    btn3 = InlineKeyboardButton(f"کوکتل موهیتو - {prices['cocktail_mojito'][1]} تومان", callback_data="cocktail_mojito")
    btn_back = InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")
    markup.add(btn1, btn2, btn3, btn_back)
    return markup

# منوی انتخاب تعداد نفرات
def select_count_menu():
    markup = InlineKeyboardMarkup(row_width=3)
    for i in range(1, 6):
        markup.add(InlineKeyboardButton(f"{i}️⃣ نفر", callback_data=f"count_{i}"))
    markup.add(InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu"))
    return markup

# منوی انتخاب تعداد برای هر محصول (1 تا 10)
def select_item_count_menu(item):
    markup = InlineKeyboardMarkup(row_width=3)
    for i in range(1, 11):
        markup.add(InlineKeyboardButton(f"{i}", callback_data=f"select_count_{item}_{i}"))
    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu"))
    return markup

# ذخیره سفارشات با تعداد
def add_to_order(chat_id, item, count):
    if chat_id not in user_orders:
        user_orders[chat_id] = {}
    user_orders[chat_id][item] = count
    logging.info(f"سفارش اضافه شد: {item} - {count} عدد برای {chat_id}")

# ویرایش فاکتور
def edit_order(chat_id):
    if chat_id not in user_orders or not user_orders[chat_id]:
        bot.send_message(chat_id, "⛔ هنوز سفارشی ثبت نکرده‌اید!", reply_markup=main_menu())
        return
    markup = InlineKeyboardMarkup()
    for item, count in user_orders[chat_id].items():
        markup.add(InlineKeyboardButton(f"❌ حذف {prices[item][0]} ({count} عدد)", callback_data=f"remove_{item}"))
    markup.add(InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu"))
    bot.send_message(chat_id, "📝 مواردی که می‌خواهید حذف کنید را انتخاب کنید:", reply_markup=markup)

# حذف آیتم از فاکتور
def remove_item(call):
    chat_id = call.message.chat.id
    item = call.data.split("_", 1)[1]
    if item in user_orders[chat_id]:
        count = user_orders[chat_id][item]
        del user_orders[chat_id][item]
        bot.answer_callback_query(call.id, f"❌ {prices[item][0]} ({count} عدد) از سفارش شما حذف شد.")
    bot.delete_message(chat_id, call.message.message_id)
    if user_orders[chat_id]:
        markup = InlineKeyboardMarkup()
        for remaining_item, remaining_count in user_orders[chat_id].items():
            markup.add(InlineKeyboardButton(f"❌ حذف {prices[remaining_item][0]} ({remaining_count} عدد)", callback_data=f"remove_{remaining_item}"))
        markup.add(InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu"))
        bot.send_message(chat_id, "📝 موارد باقی‌مونده برای حذف:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "⛔ همه سفارشات حذف شدند!", reply_markup=back_to_menu())

# نمایش فاکتور نهایی برای انتخاب نحوه ورود
def show_invoice(chat_id):
    if chat_id not in user_orders or not user_orders[chat_id]:
        bot.send_message(chat_id, "⛔ شما هنوز سفارشی ثبت نکرده‌اید!", reply_markup=main_menu())
        return
    if chat_id not in user_counts or user_counts[chat_id] <= 0:
        bot.send_message(chat_id, "⛔ شما تعداد نفرات رو انتخاب نکردید! لطفاً ابتدا تعداد نفرات رو مشخص کنید.", reply_markup=main_menu())
        return
    markup = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("🚗 با ماشین میام", callback_data="with_car")
    btn2 = InlineKeyboardButton("🚶 بدون ماشین میام", callback_data="without_car")
    markup.add(btn1, btn2)
    bot.send_message(chat_id, "لطفاً نحوه ورود خودتون رو انتخاب کنید:", reply_markup=markup)

# نمایش فاکتور نهایی با جزئیات
def show_final_invoice(chat_id, entry_type_text):
    base_total, entry_fee, total = calculate_total(chat_id)
    items_list = "\n".join([f"{prices[item][0]} ({count} عدد)" for item, count in user_orders[chat_id].items()])
    invoice_text = (
        f"📝 سفارش شما:\n"
        f"{items_list}\n\n"
        f"💵 هزینه سفارش‌ها: {base_total} تومان\n"
        f"🚪 هزینه ورودی و سرویس: {entry_fee} تومان\n"
        f"💰 مجموع پرداختی شما: {total} تومان\n\n"
        f"💳 لطفاً مبلغ را به شماره کارت <code>5892101481952691</code> زهرا دوستدار واریز کنید و فیش را ارسال کنید."
    )
    bot.send_message(chat_id, invoice_text, reply_markup=back_to_menu(), parse_mode="HTML")

# مدیریت دریافت فیش پرداخت
@bot.message_handler(content_types=['photo'])
def handle_payment_receipt(message):
    chat_id = message.chat.id
    if chat_id not in user_orders or not user_orders[chat_id]:
        bot.send_message(chat_id, "⛔ شما هنوز سفارشی ثبت نکرده‌اید!", reply_markup=back_to_menu())
        return
    if user_entry_type.get(chat_id) is None:
        bot.send_message(chat_id, "⛔ لطفاً ابتدا نحوه ورود خودتون رو انتخاب کنید!", reply_markup=back_to_menu())
        return

    payment_id = str(uuid.uuid4())[:8]
    base_total, entry_fee, total = calculate_total(chat_id)
    items_list = "\n".join([f"{prices[item][0]} ({count} عدد)" for item, count in user_orders[chat_id].items()])
    entry_text = "با ماشین" if user_entry_type[chat_id] == "with_car" else "بدون ماشین"
    bot.send_message(chat_id, "✅ فیش شما دریافت شد، لطفاً منتظر بمانید تا بررسی شود.")

    pending_payments[payment_id] = {
        "user_id": chat_id,
        "username": message.from_user.first_name if message.from_user.first_name else "کاربر",
        "total": total,
        "items": items_list,
        "file_id": message.photo[-1].file_id,
        "entry_type": entry_text
    }

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ تأیید پرداخت", callback_data=f"approve_{payment_id}"))
    markup.add(InlineKeyboardButton("❌ رد پرداخت", callback_data=f"reject_{payment_id}"))
    caption = (
        f"🆕 پرداخت جدید دریافت شد!\n"
        f"👤 کاربر: {message.from_user.first_name if message.from_user.first_name else 'کاربر'}\n"
        f"👥 تعداد نفرات: {user_counts[chat_id]}\n"
        f"📝 سفارشات:\n{items_list}\n"
        f"🚗 نحوه ورود: {entry_text}\n"
        f"💰 مبلغ کل: {total} تومان\n\n"
        "📌 لطفاً بررسی کنید."
    )
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup)

# اجرای ربات
def run_bot():
    while True:
        try:
            set_persistent_menu()
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            logging.error(f"خطا در اجرا: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
