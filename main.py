import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import time
import logging
import uuid
from datetime import datetime

# شناسه ادمین
ADMIN_ID = 99510185

# راه‌اندازی سرور Flask
from background import keep_alive
keep_alive()

# تنظیم لاگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

8130794230:AAHWF5jJ4mndYc1W8t2g_YIBbEGwjnV8sd4
TOKEN = ""
bot = telebot.TeleBot(TOKEN)

# دیکشنری‌ها
pending_payments = {}
user_orders = {}
user_counts = {}
user_entry_type = {}

# قیمت‌ها
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
    "cocktail_orange": ("کوکتل پرتقال", 100),
    "cocktail_mojito": ("کوکتل موهیتو", 100)
}

# هزینه‌ها
ENTRY_FEE_WITH_CAR = 50
ENTRY_FEE_BASE = 100

# تنظیم منوی همیشگی
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

# دکمه بازگشت به منو
def back_to_menu():
    markup = InlineKeyboardMarkup()
    btn_back = InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")
    markup.add(btn_back)
    return markup

# دکمه ارسال فیش
def send_receipt_button():
    markup = InlineKeyboardMarkup()
    btn_send = InlineKeyboardButton("📤 ارسال فیش", callback_data="send_receipt")
    markup.add(btn_send)
    return markup

# نمایش زمان باقی‌مونده
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

# منوی اصلی
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

# خوش‌آمدگویی
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_orders[chat_id] = {}
    user_counts[chat_id] = 0
    user_entry_type[chat_id] = None
    first_name = message.from_user.first_name or "دوست عزیز"
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

# نمایش منو
@bot.message_handler(commands=['menu'])
def show_menu(message):
    bot.send_message(message.chat.id, "📜 منوی اصلی:", reply_markup=main_menu())

# نمایش تاریخ جشن
@bot.message_handler(commands=['event'])
def show_event(message):
    show_event_timer(message.chat.id)

# مشاهده فاکتور
@bot.message_handler(commands=['checkout'])
def checkout_command(message):
    show_invoice(message.chat.id)

# ویرایش فاکتور
@bot.message_handler(commands=['edit'])
def edit_command(message):
    edit_order(message.chat.id)

# نمایش منوی کوکتل
@bot.message_handler(commands=['cocktail'])
def cocktail_command(message):
    bot.send_message(message.chat.id, "🍹 کوکتل‌ها:\n👇 یکی از گزینه‌ها رو انتخاب کن:", reply_markup=cocktail_menu())

# محاسبه کل مبلغ
def calculate_total(chat_id):
    if chat_id not in user_orders or not user_orders[chat_id] or chat_id not in user_counts or user_counts[chat_id] <= 0:
        return 0, 0, 0
    base_total = sum(prices[item][1] * count for item, count in user_orders[chat_id].items())
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
            bot.send_message(chat_id, "🍽 پیش‌غذاها:\n👇 گزینه‌ها رو انتخاب کن:", reply_markup=starter_menu())
        elif call.data == "main_course":
            bot.send_message(chat_id, "🥘 غذای اصلی:\n👇 گزینه‌ها رو انتخاب کن:", reply_markup=main_course_menu())
        elif call.data == "cocktail":
            bot.send_message(chat_id, "🍹 کوکتل‌ها:\n👇 گزینه‌ها رو انتخاب کن:", reply_markup=cocktail_menu())
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
        elif call.data == "send_receipt":
            bot.edit_message_text("📤 لطفا عکس فیش رو بفرست همینجا و منتظر بمون 😎", chat_id, call.message.message_id)
        elif call.data.startswith("approve_") or call.data.startswith("reject_"):
            admin_id = call.message.chat.id
            if admin_id != ADMIN_ID:
                bot.answer_callback_query(call.id, "⛔ شما اجازه ندارید!")
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
                bot.send_message(user_id, "✅ واریزی شما تأیید شد. بزودی تماس می‌گیریم.")
                bot.send_message(ADMIN_ID, f"✅ پرداخت {username} تأیید شد.")
                bot.answer_callback_query(call.id, "✅ پرداخت تأیید شد!")
            else:
                bot.send_message(user_id, "❌ پرداخت رد شد. با @Shabahang67 تماس بگیرید.")
                bot.send_message(ADMIN_ID, f"❌ پرداخت {username} رد شد.")
                bot.answer_callback_query(call.id, "❌ پرداخت رد شد!")
            bot.edit_message_reply_markup(ADMIN_ID, call.message.message_id, reply_markup=None)
        elif call.data.startswith("select_count_"):
            parts = call.data.split("_")
            item = "_".join(parts[2:-1])
            count = int(parts[-1])
            add_to_order(chat_id, item, count)
            bot.send_message(chat_id, f"✅ {prices[item][0]} ({count} عدد) اضافه شد.", reply_markup=back_to_menu())
        elif call.data in prices:
            bot.send_message(chat_id, f"👇 تعداد {prices[call.data][0]} را مشخص کن:", reply_markup=select_item_count_menu(call.data))
        elif call.data == "back_to_menu":
            bot.edit_message_text("📜 منوی اصلی:", chat_id, call.message.id, reply_markup=main_menu())
    except Exception as e:
        logging.error(f"خطا: {e}")
        bot.send_message(chat_id, "⚠️ مشکل پیش اومد، دوباره امتحان کن!")

# تغییر تعداد نفرات
def update_count(call):
    chat_id = call.message.chat.id
    count = int(call.data.split("_")[1])
    user_counts[chat_id] = count
    bot.edit_message_text(f"✅ تعداد نفرات: {count}", chat_id, call.message.message_id, reply_markup=back_to_menu())

# منوی پیش‌غذا
def starter_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton(f"زیتون ساده - {prices['starter_olive'][1]} تومان", callback_data="starter_olive")
    btn2 = InlineKeyboardButton(f"زیتون پرورده - {prices['starter_olive_stuffed'][1]} تومان", callback_data="starter_olive_stuffed")
    btn3 = InlineKeyboardButton(f"ماست و خیار - {prices['starter_yogurt'][1]} تومان", callback_data="starter_yogurt")
    btn4 = InlineKeyboardButton(f"شور - {prices['starter_pickle'][1]} تومان", callback_data="starter_pickle")
    btn5 = InlineKeyboardButton(f"خیار و گوجه - {prices['starter_cucumber_tomato'][1]} تومان", callback_data="starter_cucumber_tomato")
    btn_back = InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn_back)
    return markup

# منوی غذای اصلی
def main_course_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton(f"کشک بادمجان - {prices['main_kashk'][1]} تومان", callback_data="main_kashk")
    btn2 = InlineKeyboardButton(f"ماکارونی - {prices['main_pasta'][1]} تومان", callback_data="main_pasta")
    btn3 = InlineKeyboardButton(f"بادکوبه - {prices['main_badkobe'][1]} تومان", callback_data="main_badkobe")
    btn_back = InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")
    markup.add(btn1, btn2, btn3, btn_back)
    return markup

# منوی کوکتل
def cocktail_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton(f"کوکتل دوغ - {prices['cocktail_dough'][1]} تومان", callback_data="cocktail_dough")
    btn2 = InlineKeyboardButton(f"کوکتل پرتقال - {prices['cocktail_orange'][1]} تومان", callback_data="cocktail_orange")
    btn3 = InlineKeyboardButton(f"کوکتل موهیتو - {prices['cocktail_mojito'][1]} تومان", callback_data="cocktail_mojito")
    btn_back = InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")
    markup.add(btn1, btn2, btn3, btn_back)
    return markup

# منوی تعداد نفرات
def select_count_menu():
    markup = InlineKeyboardMarkup(row_width=3)
    for i in range(1, 6):
        markup.add(InlineKeyboardButton(f"{i}️⃣ نفر", callback_data=f"count_{i}"))
    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu"))
    return markup

# منوی انتخاب تعداد
def select_item_count_menu(item):
    markup = InlineKeyboardMarkup(row_width=3)
    for i in range(1, 11):
        markup.add(InlineKeyboardButton(f"{i}", callback_data=f"select_count_{item}_{i}"))
    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu"))
    return markup

# افزودن به سفارش
def add_to_order(chat_id, item, count):
    if chat_id not in user_orders:
        user_orders[chat_id] = {}
    user_orders[chat_id][item] = count

# ویرایش فاکتور
def edit_order(chat_id):
    if chat_id not in user_orders or not user_orders[chat_id]:
        bot.send_message(chat_id, "⛔ سفارشی ثبت نشده!", reply_markup=main_menu())
        return
    markup = InlineKeyboardMarkup()
    for item, count in user_orders[chat_id].items():
        markup.add(InlineKeyboardButton(f"❌ حذف {prices[item][0]} ({count} عدد)", callback_data=f"remove_{item}"))
    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu"))
    bot.send_message(chat_id, "📝 موارد قابل حذف:", reply_markup=markup)

# حذف آیتم
def remove_item(call):
    chat_id = call.message.chat.id
    item = call.data.split("_", 1)[1]
    if item in user_orders[chat_id]:
        del user_orders[chat_id][item]
        bot.answer_callback_query(call.id, f"❌ {prices[item][0]} حذف شد.")
    bot.delete_message(chat_id, call.message.message_id)
    if user_orders[chat_id]:
        markup = InlineKeyboardMarkup()
        for remaining_item, remaining_count in user_orders[chat_id].items():
            markup.add(InlineKeyboardButton(f"❌ حذف {prices[remaining_item][0]} ({remaining_count} عدد)", callback_data=f"remove_{remaining_item}"))
        markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu"))
        bot.send_message(chat_id, "📝 موارد باقی‌مونده:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "⛔ همه سفارشات حذف شدند!", reply_markup=back_to_menu())

# نمایش فاکتور
def show_invoice(chat_id):
    if chat_id not in user_orders or not user_orders[chat_id]:
        bot.send_message(chat_id, "⛔ سفارشی ثبت نشده!", reply_markup=main_menu())
        return
    if chat_id not in user_counts or user_counts[chat_id] <= 0:
        bot.send_message(chat_id, "⛔ تعداد نفرات رو مشخص کنید!", reply_markup=main_menu())
        return
    markup = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("🚗 با ماشین", callback_data="with_car")
    btn2 = InlineKeyboardButton("🚶 بدون ماشین", callback_data="without_car")
    markup.add(btn1, btn2)
    bot.send_message(chat_id, "لطفاً نحوه ورود را انتخاب کنید:", reply_markup=markup)

# نمایش فاکتور نهایی
def show_final_invoice(chat_id, entry_type_text):
    base_total, entry_fee, total = calculate_total(chat_id)
    items_list = "\n".join([f"{prices[item][0]} ({count} عدد)" for item, count in user_orders[chat_id].items()])
    invoice_text = (
        f"📝 سفارش شما:\n"
        f"{items_list}\n\n"
        f"💵 هزینه سفارش‌ها: {base_total} تومان\n"
        f"🚪 هزینه ورودی و سرویس: {entry_fee} تومان\n"
        f"💰 مجموع پرداختی: {total} تومان\n\n"
        f"<b>عزیران لطفا بعد از پرداخت کارت به کارت عکس فیش رو همینجا ارسال کنید 😎 ممنون از شما😊</b>\n"
        f"💳 مبلغ را به کارت <code>5892101481952691</code> زهرا دوستدار واریز کنید."
    )
    bot.send_message(chat_id, invoice_text, reply_markup=send_receipt_button(), parse_mode="HTML")

# مدیریت فیش
@bot.message_handler(content_types=['photo'])
def handle_payment_receipt(message):
    chat_id = message.chat.id
    if chat_id not in user_orders or not user_orders[chat_id]:
        bot.send_message(chat_id, "⛔ سفارشی ثبت نشده!", reply_markup=back_to_menu())
        return
    if user_entry_type.get(chat_id) is None:
        bot.send_message(chat_id, "⛔ نحوه ورود را انتخاب کنید!", reply_markup=back_to_menu())
        return
    payment_id = str(uuid.uuid4())[:8]
    base_total, entry_fee, total = calculate_total(chat_id)
    items_list = "\n".join([f"{prices[item][0]} ({count} عدد)" for item, count in user_orders[chat_id].items()])
    entry_text = "با ماشین" if user_entry_type[chat_id] == "with_car" else "بدون ماشین"
    bot.send_message(chat_id, "✅ فیش دریافت شد، منتظر بررسی باشید.")
    pending_payments[payment_id] = {
        "user_id": chat_id,
        "username": message.from_user.first_name or "کاربر",
        "total": total,
        "items": items_list,
        "file_id": message.photo[-1].file_id,
        "entry_type": entry_text
    }
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{payment_id}"))
    markup.add(InlineKeyboardButton("❌ رد", callback_data=f"reject_{payment_id}"))
    caption = (
        f"🆕 پرداخت جدید:\n"
        f"👤 کاربر: {message.from_user.first_name or 'کاربر'}\n"
        f"👥 نفرات: {user_counts[chat_id]}\n"
        f"📝 سفارشات:\n{items_list}\n"
        f"🚗 ورود: {entry_text}\n"
        f"💰 مبلغ: {total} تومان\n\n"
        "📌 بررسی کنید."
    )
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup)

# اجرای ربات
def run_bot():
    while True:
        try:
            set_persistent_menu()
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            logging.error(f"خطا: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
