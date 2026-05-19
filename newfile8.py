import telebot
from telebot import types
import sqlite3
import os

# ================== الإعدادات ==================
TOKEN = "8896896933:AAFqlwDkCbQEOe7bnQEmGmG6lIoQvfoDXlU"
ADMIN_ID = 8617632424
OWNER_NAME = "حافظ عبده احمد عبدالرحمن احمد"
JAIB_ACCOUNT = "784714890"
PHONE_PAY = "784714890"

bot = telebot.TeleBot(TOKEN)

if not os.path.exists( uploads ):
    os.makedirs( uploads )

def init_db():
    conn = sqlite3.connect( bot_data.db )
    cursor = conn.cursor()
    cursor.execute(   CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, status TEXT, file_path TEXT)   )
    conn.commit()
    conn.close()

init_db()

def is_subscribed(user_id):
    conn = sqlite3.connect( bot_data.db )
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row and row[0] ==  active 

def activate_user(user_id):
    conn = sqlite3.connect( bot_data.db )
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, status) VALUES (?, ?)", (user_id,  active ))
    conn.commit()
    conn.close()

# ================== المعالجات ==================
@bot.message_handler(commands=["start"])
def start(message):
    welcome_text = (
        "🚀 **أهلاً بك في منصة حافظ الرقمية!**\n\n"
        "نحن هنا لتقديم أفضل الخدمات التقنية ورفع ملفاتك بأمان وسرعة.\n"
        "💡 *ماذا يمكنك أن تفعل هنا؟*\n"
        "✅ رفع ملفات APK وتخزينها بأمان.\n"
        "✅ اشتراكات مرنة تناسب احتياجاتك.\n"
        "✅ دعم فني مباشر وسريع.\n\n"
        "👇 **اختر الخدمة التي تناسبك من الأزرار أدناه:**"
    )
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("📱 رفع ملف APK", callback_data="apk"),
          types.InlineKeyboardButton("💳 عرض باقات الاشتراك", callback_data="pay"))
    try:
        bot.send_message(message.chat.id, welcome_text, reply_markup=m, parse_mode="Markdown")
    except Exception as e:
        print(f"Error in start: {e}")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.message.chat.id
    try:
        if call.data == "apk":
            if is_subscribed(uid):
                msg = bot.send_message(uid, "📱 أرسل ملف الـ APK الآن (كمستند).")
                bot.register_next_step_handler(msg, save_apk_file)
            else:
                bot.answer_callback_query(call.id, "❌ يجب الاشتراك أولاً!")
                bot.send_message(uid, "❌ عذراً، لا يمكنك رفع الملفات. يجب عليك الاشتراك في إحدى باقاتنا أولاً.")
                
        elif call.data == "pay":
            m = types.InlineKeyboardMarkup(row_width=1)
            m.add(types.InlineKeyboardButton("💳 دفع يدوي (بالدولار)", callback_data="pay_manual"),
                  types.InlineKeyboardButton("⭐ دفع بالنجوم (تلقائي)", callback_data="pay_stars"))
            bot.edit_message_text("اختر طريقة الدفع:", uid, call.message.message_id, reply_markup=m)

        elif call.data == "pay_manual":
            m = types.InlineKeyboardMarkup(row_width=2)
            m.add(
                types.InlineKeyboardButton("🗓 أسبوعي (2$)", callback_data="manual_2"),
                types.InlineKeyboardButton("📅 شهري (3$)", callback_data="manual_3"),
                types.InlineKeyboardButton("📊 ربع سنوي (5$)", callback_data="manual_9")
            )
            bot.edit_message_text("اختر الباقة للدفع اليدوي:", uid, call.message.message_id, reply_markup=m)

        elif call.data.startswith("manual_"):
            price = call.data.split("_")[1]
            text = (f"💳 **بيانات الدفع اليدوي ({price}$):**\n\n"
                    f"يرجى التحويل إلى البيانات التالية:\n"
                    f"👤 صاحب الحساب: {OWNER_NAME}\n"
                    f"💰 حساب جيب: `{JAIB_ACCOUNT}`\n"
                    f"📱 هاتف: `{PHONE_PAY}`\n\n"
                    f"📌 أرسل صورة السند هنا ليتم تفعيل اشتراكك.")
            bot.edit_message_text(text, uid, call.message.message_id, parse_mode="Markdown")

        elif call.data == "pay_stars":
            m = types.InlineKeyboardMarkup(row_width=2)
            m.add(types.InlineKeyboardButton("🗓 أسبوعي (100⭐)", callback_data="star_100"),
                  types.InlineKeyboardButton("📅 شهري (150⭐)", callback_data="star_150"))
            bot.edit_message_text("اختر باقة النجوم:", uid, call.message.message_id, reply_markup=m)

        elif call.data.startswith("star_"):
            amount = int(call.data.split("_")[1])
            bot.send_invoice(uid, "اشتراك منصة حافظ", f"اشتراك بقيمة {amount} نجمة", "stars_pay", "XTR", [types.LabeledPrice("اشتراك", amount)])

        elif call.data.startswith("approve_"):
            user_id = call.data.split("_")[1]
            activate_user(user_id)
            bot.send_message(user_id, "✅ تم تفعيل اشتراكك يدوياً!")
            bot.answer_callback_query(call.id, "تم التفعيل")
    except Exception as e:
        print(f"Callback error: {e}")

@bot.message_handler(content_types=[ successful_payment ])
def successful_payment(message):
    activate_user(message.chat.id)
    bot.reply_to(message, "✅ شكراً! تم تفعيل اشتراكك تلقائياً.")

@bot.message_handler(content_types=[ photo ])
def handle_receipt(message):
    uid = message.chat.id
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("✅ تفعيل المستخدم", callback_data=f"approve_{uid}"))
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"💳 سند دفع من: {uid}", reply_markup=m)
    bot.reply_to(message, "⏳ تم إرسال السند، سيتم التفعيل قريباً.")

def save_apk_file(message):
    if not message.document:
        bot.send_message(message.chat.id, "❌ يرجى إرسال ملف APK.")
        return
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        save_path = f"uploads/{message.chat.id}_{message.document.file_name}"
        with open(save_path,  wb ) as new_file:
            new_file.write(downloaded_file)
        
        conn = sqlite3.connect( bot_data.db )
        conn.cursor().execute("UPDATE users SET file_path = ? WHERE user_id = ?", (save_path, message.chat.id))
        conn.commit()
        conn.close()
        
        bot.send_message(ADMIN_ID, f"📱 ملف جديد تم ربطه من المشترك: {message.chat.id}")
        bot.reply_to(message, "✅ تم رفع ملفك وربطه بنجاح في النظام!")
    except Exception as e:
        bot.reply_to(message, "❌ حدث خطأ أثناء رفع الملف. حاول لاحقاً.")
        print(f"Upload error: {e}")

if __name__ == "__main__":
    # هذا السطر هو الأهم في بيئة PythonAnywhere لتقليل أخطاء الـ 503
    bot.infinity_polling(timeout=20, long_polling_timeout=20)
