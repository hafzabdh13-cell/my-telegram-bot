import telebot
from telebot import types
import sqlite3
import os
from flask import Flask, jsonify
from threading import Thread

# ================== الإعدادات ==================
TOKEN = os.environ.get('TOKEN', "8675468296:AAFjLWMdHqHK-H3IuGFbH201xog-UWBGb3s")
ADMIN_ID = 8617632424
OWNER_NAME = "حافظ عبده احمد عبدالرحمن احمد"
JAIB_ACCOUNT = "784714890"
PHONE_PAY = "784714890"
CHANNEL_USERNAME = "@hafz45bot" 

# --- إعداد الخادم والـ API ---
app = Flask('')

@app.route('/')
def home():
    return "البوت يعمل بكامل طاقته!"

@app.route('/api/check_status/<user_id>', methods=['GET'])
def check_status(user_id):
    if is_subscribed(user_id):
        return jsonify({"user_id": user_id, "status": "active"})
    return jsonify({"user_id": user_id, "status": "inactive"})

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

t = Thread(target=run)
t.start()

bot = telebot.TeleBot(TOKEN)

if not os.path.exists('uploads'):
    os.makedirs('uploads')

# تعديل قاعدة البيانات لتشمل نوع وتاريخ الاشتراك إذا دعت الحاجة مستقبلاً
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, status TEXT, file_path TEXT)')
    conn.commit()
    conn.close()

init_db()

def is_subscribed(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row and row[0] == 'active'

def activate_user(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, status) VALUES (?, ?)", (user_id, 'active'))
    conn.commit()
    conn.close()

def deactivate_user(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, status) VALUES (?, ?)", (user_id, 'inactive'))
    conn.commit()
    conn.close()

def check_channel_sub(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        # في حال وجود خطأ بالوصول للقناة نعتبره غير مشترك لضمان عمل الاشتراك الإجباري
        return False

# دالة لإنشاء لوحة الأزرار الكاملة (ReplyKeyboardMarkup)
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_start = types.KeyboardButton("🚀 قائمة البدء")
    btn_contact = types.KeyboardButton("📞 تواصل معنا")
    markup.add(btn_start, btn_contact)
    return markup

# ================== المعالجات ==================
@bot.message_handler(commands=["start"])
def start_command(message):
    handle_start_logic(message.chat.id)

@bot.message_handler(func=lambda msg: msg.text in ["🚀 قائمة البدء", "📞 تواصل معنا"])
def handle_text_buttons(message):
    uid = message.chat.id
    if message.text == "🚀 قائمة البدء":
        handle_start_logic(uid)
    elif message.text == "📞 تواصل معنا":
        contact_text = (
            f"📞 **قسم الدعم الفني والتواصل**\n\n"
            f"👤 مالك المنصة: {OWNER_NAME}\n"
            f"📱 رقم الهاتف: `{PHONE_PAY}`\n"
            f"💬 لأي استفسار أو مشكلة، يسعدنا تواصلك معنا مباشرة."
        )
        bot.send_message(uid, contact_text, parse_mode="Markdown", reply_markup=main_keyboard())

def handle_start_logic(uid):
    if not check_channel_sub(uid):
        m = types.InlineKeyboardMarkup(row_width=1)
        m.add(types.InlineKeyboardButton("📢 اشترك في القناة أولاً", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"),
              types.InlineKeyboardButton("✅ تم الاشتراك (تأكيد)", callback_data="check_sub_again"))
        bot.send_message(uid, "⚠️ **عذراً، الوصول مقيد!**\n\nيجب عليك الاشتراك في القناة الرسمية لتتمكن من استخدام كافة ميزات المنصة.", reply_markup=m)
        return

    welcome_text = (
        "💎 **مرحباً بك في منصة حافظ الرقمية** 💎\n\n"
        "حيث تجتمع القوة، السرعة، والأمان في مكان واحد.\n\n"
        "✨ **لماذا تختارنا؟**\n"
        "🔹 **رفع وتخزين:** استضافة تطبيقاتك (APK) بجودة عالية.\n"
        "🔹 **نظام متطور:** ربط فوري وآمن بين تطبيقاتك وسيرفراتنا.\n"
        "🔹 **دعم تقني:** نحن معك خطوة بخطوة للارتقاء بمشاريعك.\n\n"
        "📍 *اختر الخدمة التي تليق بمشروعك من القائمة أدناه:* 👇"
    )
    
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("📱 رفع تطبيق APK", callback_data="apk"),
          types.InlineKeyboardButton("💳 باقات الاشتراك", callback_data="pay"))
    bot.send_message(uid, welcome_text, reply_markup=m, parse_mode="Markdown", reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.message.chat.id
    if call.data == "check_sub_again":
        if check_channel_sub(uid):
            bot.delete_message(uid, call.message.message_id)
            handle_start_logic(uid)
        else:
            bot.answer_callback_query(call.id, "❌ لم تشترك في القناة بعد!", show_alert=True)
            
    elif call.data == "apk":
        if is_subscribed(uid):
            msg = bot.send_message(uid, "📱 أرسل ملف الـ APK الآن (كمستند).", reply_markup=main_keyboard())
            bot.register_next_step_handler(msg, save_apk_file)
        else:
            bot.answer_callback_query(call.id, "❌ يجب الاشتراك أولاً!")
            bot.send_message(uid, "❌ لا يمكنك رفع الملفات، يجب الاشتراك في إحدى باقاتنا أولاً.", reply_markup=main_keyboard())
                
    elif call.data == "pay":
        m = types.InlineKeyboardMarkup(row_width=1)
        m.add(types.InlineKeyboardButton("💳 دفع يدوي (بالدولار)", callback_data="pay_manual"),
              types.InlineKeyboardButton("⭐ دفع بالنجوم (تلقائي)", callback_data="pay_stars"))
        bot.edit_message_text("اختر طريقة الدفع:", uid, call.message.message_id, reply_markup=m)

    elif call.data == "pay_manual":
        m = types.InlineKeyboardMarkup(row_width=2)
        m.add(types.InlineKeyboardButton("🗓 أسبوعي (2$)", callback_data="manual_2"),
              types.InlineKeyboardButton("📅 شهري (3$)", callback_data="manual_3"),
              types.InlineKeyboardButton("📊 ربع سنوي (5$)", callback_data="manual_5"),
              types.InlineKeyboardButton("⏳ سنوي (10$)", callback_data="manual_10"))
        bot.edit_message_text("اختر الباقة للدفع اليدوي:", uid, call.message.message_id, reply_markup=m)

    elif call.data.startswith("manual_"):
        price = call.data.split("_")[1]
        text = (f"💳 **بيانات الدفع اليدوي ({price}$):**\n\n"
                f"👤 صاحب الحساب: {OWNER_NAME}\n"
                f"💰 حساب جيب: `{JAIB_ACCOUNT}`\n"
                f"📱 هاتف: `{PHONE_PAY}`\n\n"
                f"📌 أرسل صورة السند هنا ليتم تفعيل اشتراكك.")
        bot.edit_message_text(text, uid, call.message.message_id, parse_mode="Markdown")

    elif call.data == "pay_stars":
        m = types.InlineKeyboardMarkup(row_width=1)
        m.add(types.InlineKeyboardButton("📅 شهري (150⭐)", callback_data="star_150"),
              types.InlineKeyboardButton("📊 ربع سنوي (300⭐)", callback_data="star_300"),
              types.InlineKeyboardButton("⏳ سنوي (650⭐)", callback_data="star_650"))
        bot.edit_message_text("اختر باقة النجوم المتاحة:", uid, call.message.message_id, reply_markup=m)

    elif call.data.startswith("star_"):
        amount = int(call.data.split("_")[1])
        bot.send_invoice(uid, "اشتراك منصة حافظ", f"اشتراك بقيمة {amount} نجمة", "stars_pay", "XTR", [types.LabeledPrice("اشتراك", amount)])

    # أزرار تحكم الإدارة بالتفعيل والرفض
    elif call.data.startswith("approve_"):
        parts = call.data.split("_")
        period = parts[1]
        user_id = parts[2]
        activate_user(user_id)
        
        period_text = {"week": "أسبوع", "month": "شهر", "quarter": "ربع سنة", "year": "سنة"}
        bot.send_message(user_id, f"✅ تم تفعيل اشتراكك يدوياً لمدة ({period_text.get(period, 'محددة')})!")
        bot.edit_message_caption(f"✅ تم تفعيل المستخدم {user_id} بنجاح لفترة: {period_text.get(period)}", ADMIN_ID, call.message.message_id)
        bot.answer_callback_query(call.id, "تم التفعيل بنجاح")

    elif call.data.startswith("reject_"):
        user_id = call.data.split("_")[1]
        deactivate_user(user_id)
        bot.send_message(user_id, "❌ نأسف، تم إلغاء تفعيل اشتراكك لعدم وصول أو صحة التحويل. يرجى التواصل مع الدعم.")
        bot.edit_message_caption(f"❌ تم رفض وإلغاء تفعيل المستخدم {user_id} (التحويل لم يصل).", ADMIN_ID, call.message.message_id)
        bot.answer_callback_query(call.id, "تم إلغاء التفعيل والرفض", show_alert=True)

@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    activate_user(message.chat.id)
    bot.reply_to(message, "✅ شكراً! تم تفعيل اشتراكك تلقائياً بالنجوم.", reply_markup=main_keyboard())

@bot.message_handler(content_types=['photo'])
def handle_receipt(message):
    uid = message.chat.id
    # لوحة أزرار التحكم الخاصة بالأدمن عند استلام صورة السند
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("⏱ تفعيل أسبوع", callback_data=f"approve_week_{uid}"),
        types.InlineKeyboardButton("🗓 تفعيل شهر", callback_data=f"approve_month_{uid}"),
        types.InlineKeyboardButton("📊 تفعيل ربع سنة", callback_data=f"approve_quarter_{uid}"),
        types.InlineKeyboardButton("⏳ تفعيل سنة", callback_data=f"approve_year_{uid}"),
        types.InlineKeyboardButton("❌ إلغاء (ما وصل)", callback_data=f"reject_{uid}")
    )
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"💳 سند دفع جديد من المستخدم: `{uid}`\n\nاختر مدة التفعيل أو قم بالإلغاء:", reply_markup=m, parse_mode="Markdown")
    bot.reply_to(message, "⏳ تم إرسال السند إلى الإدارة للتأكد، سيتم تفعيل باقتك فور مراجعته.", reply_markup=main_keyboard())

def save_apk_file(message):
    if not message.document:
        bot.send_message(message.chat.id, "❌ يرجى إرسال ملف APK.", reply_markup=main_keyboard())
        return
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        save_path = f"uploads/{message.chat.id}_{message.document.file_name}"
        with open(save_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        conn = sqlite3.connect('bot_data.db')
        conn.cursor().execute("UPDATE users SET file_path = ? WHERE user_id = ?", (save_path, message.chat.id))
        conn.commit()
        conn.close()
        bot.reply_to(message, "✅ تم رفع ملفك وربطه بنجاح في النظام!", reply_markup=main_keyboard())
    except Exception as e:
        bot.reply_to(message, "❌ حدث خطأ أثناء رفع الملف.", reply_markup=main_keyboard())
        print(f"Upload error: {e}")

if __name__ == "__main__":
    print("البوت يعمل بنجاح...")
    bot.infinity_polling()
