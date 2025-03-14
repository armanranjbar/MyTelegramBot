import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import time
import logging


ADMIN_ID = 6462791603


# این خط‌ها برای راه‌اندازی سرور Flask و گرفتن URL عمومی
from background import keep_alive
keep_alive()

# تنظیم لاگ برای دیباگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 🔒 توکن رباتت رو اینجا بذار
TOKEN = "8130794230:AAHWF5jJ4mndYc1W8t2g_YIBbEGwjnV8sd4"
bot = telebot.TeleBot(TOKEN)

# 📌 دیکشنری برای ذخیره سفارشات (محصول و تعداد) و تعداد نفرات
user_orders = {}  # ساختار: {chat_id: {item: count}}
user_counts = {}  # تعداد نفرات
pending_payments = {}

# 📌 قیمت‌ها
prices = {
    "starter_olive": ("🫒 زیتون", 50),
    "starter_yogurt": ("🍶 ماست", 30),
    "starter_salad": ("🥗 سالاد", 40),
    "main_pasta": ("🍝 ماکارونی", 100),
    "main_kashk": ("🍆 کشک بادمجان", 90),
    "main_potato": ("🍟 سیب‌زمینی", 70)
}

# 📌 تنظیم منوی همیشگی
def set_persistent_menu():
    commands = [
        BotCommand("start", "🔄 شروع مجدد"),
        BotCommand("menu", "📜 نمایش منو"),
        BotCommand("checkout", "💳 مشاهده فاکتور"),
        BotCommand("edit", "📝 ویرایش فاکتور"),
    ]
    bot.set_my_commands(commands)

# 📌 دکمه "🔙 بازگشت به منو"
def back_to_menu():
    markup = InlineKeyboardMarkup()
    btn_back = InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")
    markup.add(btn_back)
    return markup

# 🎨 ایجاد منوی اصلی
def main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("🍽 پیش‌غذا", callback_data="starter")
    btn2 = InlineKeyboardButton("🥘 غذای اصلی", callback_data="main_course")
    btn3 = InlineKeyboardButton("👥 تعداد نفرات", callback_data="select_count")
    btn4 = InlineKeyboardButton("📝 ویرایش فاکتور", callback_data="edit_order")
    btn5 = InlineKeyboardButton("💳 پرداخت نهایی", callback_data="checkout")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    return markup

# ✅ وقتی کاربر /start بزنه، عکس و متن خوشامدگویی نمایش داده بشه
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_orders[chat_id] = {}  # دیکشنری برای ذخیره محصول و تعداد
    user_counts[chat_id] = 1  # مقدار پیش‌فرض: 1 نفر

    first_name = message.from_user.first_name if message.from_user.first_name else "دوست عزیز"

    # کپشن خوشامدگویی
    welcome_caption = (
        f"سلام {first_name} جان 😍\n"
        "خیلی خوشحالیم که مارو انتخاب کردی 🎉\n\n"
        "امیدوارم یک تجربه خفن و باحال رو با ما تجربه کنی🤩\n"
        "از پیش‌غذا تا غذای اصلی، همه‌چیز اینجاست!\n"
        "با چند کلیک ساده سفارش بده و لذت ببر! 😋\n\n"
        "📜 برای شروع، یکی از گزینه‌های زیر رو انتخاب کن:"
    )

    # ارسال عکس با کپشن
    try:
        with open("welcome_image.jpg", "rb") as photo:
            bot.send_photo(chat_id, photo, caption=welcome_caption, reply_markup=main_menu())
    except FileNotFoundError:
        # اگه فایل نبود، فقط متن رو بفرست
        bot.send_message(chat_id, welcome_caption, reply_markup=main_menu())
        logging.warning("عکس welcome_image.jpg پیدا نشد! لطفاً فایل را در مسیر درست قرار دهید.")

    set_persistent_menu()

# ✅ نمایش منو با /menu
@bot.message_handler(commands=['menu'])
def show_menu(message):
    bot.send_message(message.chat.id, "📜 منوی اصلی:", reply_markup=main_menu())

# ✅ مشاهده فاکتور با /checkout
@bot.message_handler(commands=['checkout'])
def checkout_command(message):
    show_invoice(message.chat.id)

# ✅ ویرایش فاکتور با /edit
@bot.message_handler(commands=['edit'])
def edit_command(message):
    edit_order(message.chat.id)

# 🎯 واکنش به دکمه‌ها
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    logging.info(f"دکمه زده شد: {call.data}")

    try:
        # برای دکمه‌های اصلی، همیشه پیام جدید بفرست
        if call.data == "starter":
            bot.send_message(chat_id, "🍽 پیش‌غذاهای موجود:\n👇 یکی از گزینه‌های زیر رو انتخاب کن:", reply_markup=starter_menu())
        elif call.data == "main_course":
            bot.send_message(chat_id, "🥘 غذای اصلی:\n👇 یکی از گزینه‌های زیر رو انتخاب کن:", reply_markup=main_course_menu())
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
        # فقط برای back_to_menu از edit_message_text استفاده کن
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
        else:
            logging.warning(f"دکمه ناشناخته: {call.data}")
    except Exception as e:
        logging.error(f"خطا در پردازش دکمه: {e}")
        bot.send_message(chat_id, "⚠️ یه مشکلی پیش اومد، لطفاً دوباره امتحان کن!")

# 📌 تغییر تعداد نفرات
def update_count(call):
    chat_id = call.message.chat.id
    count = int(call.data.split("_")[1])
    user_counts[chat_id] = count
    bot.edit_message_text(f"✅ تعداد نفرات تنظیم شد: {count} نفر", chat_id, call.message.id, reply_markup=back_to_menu())

# 📌 منوی انتخاب پیش‌غذا
def starter_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("🫒 زیتون - 50 تومان", callback_data="starter_olive")
    btn2 = InlineKeyboardButton("🍶 ماست - 30 تومان", callback_data="starter_yogurt")
    btn3 = InlineKeyboardButton("🥗 سالاد - 40 تومان", callback_data="starter_salad")
    btn_back = InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")
    markup.add(btn1, btn2, btn3, btn_back)
    return markup

# 📌 منوی انتخاب غذای اصلی
def main_course_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("🍝 ماکارونی - 100 تومان", callback_data="main_pasta")
    btn2 = InlineKeyboardButton("🍆 کشک بادمجان - 90 تومان", callback_data="main_kashk")
    btn3 = InlineKeyboardButton("🍟 سیب‌زمینی - 70 تومان", callback_data="main_potato")
    btn_back = InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")
    markup.add(btn1, btn2, btn3, btn_back)
    return markup

# 📌 منوی انتخاب تعداد نفرات
def select_count_menu():
    markup = InlineKeyboardMarkup(row_width=3)
    for i in range(1, 6):
        markup.add(InlineKeyboardButton(f"{i}️⃣ نفر", callback_data=f"count_{i}"))
    markup.add(InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu"))
    return markup

# 📌 منوی انتخاب تعداد برای هر محصول (1 تا 10)
def select_item_count_menu(item):
    markup = InlineKeyboardMarkup(row_width=3)
    for i in range(1, 11):
        markup.add(InlineKeyboardButton(f"{i}", callback_data=f"select_count_{item}_{i}"))
    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu"))
    return markup

# 📌 ذخیره سفارشات با تعداد
def add_to_order(chat_id, item, count):
    if chat_id not in user_orders:
        user_orders[chat_id] = {}
    user_orders[chat_id][item] = count
    logging.info(f"سفارش اضافه شد: {item} - {count} عدد برای {chat_id}")

# 📌 ویرایش فاکتور
def edit_order(chat_id):
    if chat_id not in user_orders or not user_orders[chat_id]:
        bot.send_message(chat_id, "⛔ هنوز سفارشی ثبت نکرده‌اید!", reply_markup=main_menu())
        return

    markup = InlineKeyboardMarkup()
    for item, count in user_orders[chat_id].items():
        markup.add(InlineKeyboardButton(f"❌ حذف {prices[item][0]} ({count} عدد)", callback_data=f"remove_{item}"))
    markup.add(InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu"))

    bot.send_message(chat_id, "📝 مواردی که می‌خواهید حذف کنید را انتخاب کنید:", reply_markup=markup)

# 📌 حذف آیتم از فاکتور
def remove_item(call):
    chat_id = call.message.chat.id
    item = call.data.split("_", 1)[1]  # کل بخش بعد از "remove_" رو بگیر
    logging.info(f"تلاش برای حذف: {item} از {chat_id}")

    # اول حذف رو انجام بده
    if item in user_orders[chat_id]:
        count = user_orders[chat_id][item]
        del user_orders[chat_id][item]
        bot.answer_callback_query(call.id, f"❌ {prices[item][0]} ({count} عدد) از سفارش شما حذف شد.")
        logging.info(f"آیتم حذف شد: {item} از {chat_id}")
    else:
        bot.answer_callback_query(call.id, "⚠️ این آیتم قبلاً حذف شده!")
        logging.info(f"آیتم قبلاً حذف شده بود: {item} از {chat_id}")

    # حالا پیام قبلی رو حذف کن (اگه ممکن باشه)
    try:
        bot.delete_message(chat_id, call.message.message_id)
        logging.info(f"پیام قبلی حذف شد: {call.message.message_id}")
    except Exception as e:
        logging.warning(f"نمی‌تونم پیام قبلی رو حذف کنم: {e}")

    # ارسال پیام جدید با لیست به‌روز
    if user_orders[chat_id]:
        markup = InlineKeyboardMarkup()
        for remaining_item, remaining_count in user_orders[chat_id].items():
            markup.add(InlineKeyboardButton(f"❌ حذف {prices[remaining_item][0]} ({remaining_count} عدد)", callback_data=f"remove_{remaining_item}"))
        markup.add(InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu"))
        bot.send_message(chat_id, "📝 موارد باقی‌مونده برای حذف:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "⛔ همه سفارشات حذف شدند!", reply_markup=back_to_menu())

# 📌 نمایش فاکتور نهایی
def show_invoice(chat_id):
    if chat_id not in user_orders or not user_orders[chat_id]:
        bot.send_message(chat_id, "⛔ شما هنوز سفارشی ثبت نکرده‌اید!", reply_markup=main_menu())
        return

    total = sum(prices[item][1] * count for item, count in user_orders[chat_id].items()) * user_counts[chat_id]
    items_list = "\n".join([f"{prices[item][0]} ({count} عدد)" for item, count in user_orders[chat_id].items()])

    bot.send_message(chat_id, f"📝 فاکتور نهایی شما برای {user_counts[chat_id]} نفر:\n{items_list}\n💰 مجموع: {total} تومان\n\n💳 لطفاً مبلغ را به شماره کارت **1234-5678-9012-3456** واریز کنید و فیش را ارسال کنید.", reply_markup=back_to_menu())




# 📌 دریافت فیش پرداخت از کاربر
@bot.message_handler(content_types=['photo'])
def handle_payment_receipt(message):
    chat_id = message.chat.id

    if chat_id not in user_orders or not user_orders[chat_id]:
        bot.send_message(chat_id, "⛔ شما هنوز سفارشی ثبت نکرده‌اید!", reply_markup=back_to_menu())
        return

    # ذخیره اطلاعات سفارش
    total = sum(prices[item][1] * count for item, count in user_orders[chat_id].items()) * user_counts[chat_id]
    items_list = "\n".join([f"{prices[item][0]} ({count} عدد)" for item, count in user_orders[chat_id].items()])

    # ارسال پیام به کاربر
    bot.send_message(chat_id, "✅ فیش شما دریافت شد، لطفاً منتظر بمانید تا بررسی شود.")

    # ذخیره اطلاعات پرداخت در لیست بررسی
    pending_payments[message.photo[-1].file_id] = {  # 🟢 اینجا `pending_payments` مقداردهی شده
        "user_id": chat_id,
        "username": message.from_user.first_name,
        "total": total,
        "items": items_list
    }

    # دکمه‌های تأیید و رد
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ تأیید پرداخت", callback_data=f"approve_{message.photo[-1].file_id}"))
    markup.add(InlineKeyboardButton("❌ رد پرداخت", callback_data=f"reject_{message.photo[-1].file_id}"))

    # ارسال اطلاعات برای ادمین همراه با دکمه‌ها
    caption = (f"🆕 پرداخت جدید دریافت شد!\n"
               f"👤 کاربر: {message.from_user.first_name}\n"
               f"👥 تعداد نفرات: {user_counts[chat_id]}\n"
               f"📝 سفارشات:\n{items_list}\n"
               f"💰 مبلغ واریزی: {total} تومان\n\n"
               "📌 لطفاً بررسی کنید.")

    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup)

# 📌 تأیید یا رد پرداخت توسط ادمین
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def process_payment_decision(call):
    admin_id = call.message.chat.id
    if admin_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ شما اجازه انجام این عملیات را ندارید.")
        return

    # استخراج اطلاعات پرداخت
    file_id = call.data.split("_")[1]
    payment_info = pending_payments.pop(file_id, None)

    if not payment_info:
        bot.answer_callback_query(call.id, "⛔ اطلاعات پرداخت یافت نشد.")
        return

    user_id = payment_info["user_id"]
    username = payment_info["username"]

    if call.data.startswith("approve_"):
        # تأیید پرداخت
        bot.send_message(user_id, "✅ پرداخت شما تأیید شد! سفارش شما در حال آماده‌سازی است. 🎉")
        bot.send_message(ADMIN_ID, f"✅ پرداخت کاربر {username} تأیید شد. سفارش در حال پردازش است.")
        bot.answer_callback_query(call.id, "✅ پرداخت تأیید شد!")
    else:
        # رد پرداخت
        bot.send_message(user_id, "❌ پرداخت شما تأیید نشد. لطفاً با پشتیبانی تماس بگیرید.")
        bot.send_message(ADMIN_ID, f"❌ پرداخت کاربر {username} رد شد.")
        bot.answer_callback_query(call.id, "❌ پرداخت رد شد!")

    # حذف دکمه‌ها از پیام اصلی
    try:
        bot.edit_message_reply_markup(ADMIN_ID, call.message.message_id, reply_markup=None)
    except Exception as e:
        logging.error(f"خطا در حذف دکمه‌ها: {e}")



# 🟢 اجرای ربات با مدیریت خطا
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
