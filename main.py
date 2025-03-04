import logging
import sqlite3
import random
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import string

# 🔑 تنظیمات اصلی
TOKEN = "Robot Token"
ADMIN_ID = 227975536  # آیدی عددی مدیر
REQUIRED_CHANNEL = "@your_channel"  # آیدی کانال اجباری (مثال: @your_channel)
CHANNEL_TITLE = "کانال رسمی"  # عنوان کانال برای نمایش به کاربر

# راه‌اندازی ربات
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# اتصال به دیتابیس SQLite
conn = sqlite3.connect("partners.db")
cursor = conn.cursor()

# ایجاد جدول‌های موردنیاز
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    partner_id INTEGER DEFAULT NULL,
    unique_code TEXT UNIQUE,
    waiting_for_code INTEGER DEFAULT 0
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    partner_id INTEGER,
    question TEXT,
    answer TEXT DEFAULT NULL
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER,
    receiver_id INTEGER,
    message TEXT DEFAULT NULL,
    media_type TEXT DEFAULT NULL,
    media_id TEXT DEFAULT NULL
)''')

conn.commit()

# لیست سوالات چالشی
questions = [
    "اگر یک آرزوی غیرممکن داشتی، چی بود؟",
    "بزرگترین ترس زندگیت چیه؟",
    "بهترین خاطره‌ای که با پارتنرت داری چیه؟",
    "اگر می‌تونستی یک چیز رو در زندگیت تغییر بدی، چی بود؟"
]

def generate_unique_code():
    """ تولید کد یکتا برای کاربر """
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

async def check_subscription(user_id):
    """ بررسی وضعیت عضویت کاربر در کانال اجباری """
    try:
        member = await bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"خطا در بررسی عضویت کاربر {user_id}: {e}")
        return False

def get_subscription_keyboard():
    """ ایجاد دکمه برای عضویت در کانال """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🔔 عضویت در {CHANNEL_TITLE}", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton(text="✅ بررسی مجدد عضویت", callback_data="check_subscription")]
        ]
    )
    return keyboard

async def check_user_subscription(message: types.Message):
    """بررسی عضویت کاربر و ارسال پیام در صورت عدم عضویت"""
    user_id = message.from_user.id
    is_subscribed = await check_subscription(user_id)
    
    if not is_subscribed:
        subscription_keyboard = get_subscription_keyboard()
        await message.answer(
            f"⚠️ برای استفاده از ربات، ابتدا باید در کانال {CHANNEL_TITLE} عضو شوید.",
            reply_markup=subscription_keyboard
        )
        return False
    
    return True

async def send_question(user_id, partner_id):
    """ ارسال سوال چالشی به دو پارتنر """
    question = random.choice(questions)
    
    # حذف سوالات قبلی بدون پاسخ برای جلوگیری از تداخل
    cursor.execute("DELETE FROM questions WHERE user_id = ? AND partner_id = ? AND answer IS NULL", (user_id, partner_id))
    cursor.execute("DELETE FROM questions WHERE user_id = ? AND partner_id = ? AND answer IS NULL", (partner_id, user_id))
    conn.commit()
    
    question_id_1 = None
    question_id_2 = None
    
    # ایجاد سوال جدید برای هر دو کاربر
    cursor.execute("INSERT INTO questions (user_id, partner_id, question) VALUES (?, ?, ?)", (user_id, partner_id, question))
    question_id_1 = cursor.lastrowid
    
    cursor.execute("INSERT INTO questions (user_id, partner_id, question) VALUES (?, ?, ?)", (partner_id, user_id, question))
    question_id_2 = cursor.lastrowid
    
    conn.commit()
    
    await bot.send_message(user_id, f"💬 سوال جدید: {question}\n✏️ پاسخ خود را ارسال کنید.")
    await bot.send_message(partner_id, f"💬 سوال جدید: {question}\n✏️ پاسخ خود را ارسال کنید.")
    
    # ارسال پیام به ادمین
    await bot.send_message(ADMIN_ID, f"🔔 سوال جدید به کاربران {user_id} و {partner_id} ارسال شد:\n{question}")

async def scheduled_questions():
    """ ارسال سوال هر ۲ ساعت یک بار """
    while True:
        cursor.execute("SELECT user_id, partner_id FROM users WHERE partner_id IS NOT NULL")
        pairs = cursor.fetchall()

        for user_id, partner_id in pairs:
            await send_question(user_id, partner_id)

        await asyncio.sleep(7200)  # هر ۲ ساعت

@dp.message(Command("start"))
async def start(message: types.Message):
    """ ثبت‌نام و ایجاد کد اختصاصی """
    user_id = message.from_user.id
    
    # بررسی عضویت کاربر در کانال
    is_subscribed = await check_subscription(user_id)
    if not is_subscribed:
        subscription_keyboard = get_subscription_keyboard()
        await message.answer(
            f"سلام {message.from_user.first_name}!\n\n⚠️ برای استفاده از ربات، ابتدا باید در کانال {CHANNEL_TITLE} عضو شوید.",
            reply_markup=subscription_keyboard
        )
        return
    
    # ادامه روند معمول
    cursor.execute("SELECT unique_code, partner_id FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()

    if not user_data:
        unique_code = generate_unique_code()
        cursor.execute("INSERT INTO users (user_id, unique_code) VALUES (?, ?)", (user_id, unique_code))
        conn.commit()
        partner_id = None
    else:
        unique_code, partner_id = user_data

    partner_status = "❌ هیچ پارتنری ندارید." if not partner_id else f"✅ شما متصل هستید به: [{partner_id}](tg://user?id={partner_id})"

    # ایجاد دکمه‌های منوی اصلی
    menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/connect - 🔗 اتصال به پارتنر")],
            [KeyboardButton(text="/manage - 👤 مدیریت پارتنر")],
            [KeyboardButton(text="/status - 📜 مشاهده وضعیت")],
        ],
        resize_keyboard=True
    )

    await message.answer(
        f"سلام {message.from_user.first_name}!\n\n🔑 **کد اختصاصی شما:** {unique_code}\n📨 این کد را برای پارتنرت بفرست تا متصل شود.\n\n{partner_status}\n\n"
        f"برای اتصال به پارتنر روی دکمه '/connect - 🔗 اتصال به پارتنر' کلیک کنید یا دستور /connect را ارسال کنید.",
        parse_mode="Markdown", reply_markup=menu
    )
    
    # اطلاع به ادمین
    await bot.send_message(
        ADMIN_ID, 
        f"🔔 کاربر جدید:\nنام: {message.from_user.first_name}\nآیدی: {user_id}\nیوزرنیم: @{message.from_user.username or 'ندارد'}"
    )

@dp.message(Command("connect"))
async def connect_partner_cmd(message: types.Message):
    """ مدیریت درخواست اتصال به پارتنر """
    # بررسی عضویت کاربر در کانال
    if not await check_user_subscription(message):
        return
    
    user_id = message.from_user.id
    cursor.execute("SELECT partner_id FROM users WHERE user_id=?", (user_id,))
    partner = cursor.fetchone()
    
    if partner and partner[0]:
        await message.answer("⚠️ شما در حال حاضر به یک پارتنر متصل هستید. برای اتصال به پارتنر جدید، ابتدا ارتباط فعلی را قطع کنید.")
        return
    
    # فعال کردن حالت انتظار برای کد
    cursor.execute("UPDATE users SET waiting_for_code = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    
    await message.answer("🔍 لطفاً کد اختصاصی پارتنر خود را وارد کنید:")

@dp.message(Command("manage"))
async def manage_partner_cmd(message: types.Message):
    """ مدیریت پارتنر """
    # بررسی عضویت کاربر در کانال
    if not await check_user_subscription(message):
        return
    
    user_id = message.from_user.id
    cursor.execute("SELECT partner_id FROM users WHERE user_id=?", (user_id,))
    partner = cursor.fetchone()
    
    if not partner or not partner[0]:
        await message.answer("⚠️ شما هنوز به پارتنری متصل نشده‌اید.")
        return
    
    # ایجاد دکمه برای قطع ارتباط
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ قطع ارتباط با پارتنر", callback_data="disconnect_partner")]
        ]
    )
    
    await message.answer("🛠 مدیریت پارتنر:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "disconnect_partner")
async def disconnect_partner(callback: types.CallbackQuery):
    """ قطع ارتباط با پارتنر """
    user_id = callback.from_user.id
    cursor.execute("SELECT partner_id FROM users WHERE user_id=?", (user_id,))
    partner = cursor.fetchone()
    
    if partner and partner[0]:
        partner_id = partner[0]
        
        # قطع ارتباط دو طرفه
        cursor.execute("UPDATE users SET partner_id = NULL WHERE user_id = ?", (user_id,))
        cursor.execute("UPDATE users SET partner_id = NULL WHERE user_id = ?", (partner_id,))
        conn.commit()
        
        await callback.message.edit_text("✅ ارتباط شما با پارتنر قطع شد.")
        await bot.send_message(partner_id, "⚠️ پارتنر شما ارتباط را قطع کرد.")
        
        # اطلاع به ادمین
        await bot.send_message(ADMIN_ID, f"🔔 کاربر {user_id} ارتباط خود را با کاربر {partner_id} قطع کرد.")
    else:
        await callback.message.edit_text("⚠️ شما به پارتنری متصل نیستید.")
    
    await callback.answer()

@dp.callback_query(lambda c: c.data == "check_subscription")
async def check_subscription_callback(callback: types.CallbackQuery):
    """ بررسی مجدد عضویت کاربر در کانال """
    user_id = callback.from_user.id
    is_subscribed = await check_subscription(user_id)
    
    if is_subscribed:
        await callback.message.edit_text("✅ عضویت شما در کانال تایید شد. حالا می‌توانید از ربات استفاده کنید!")
        await callback.answer("✅ عضویت تایید شد")
        
        # ارسال منوی اصلی
        menu = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="/connect - 🔗 اتصال به پارتنر")],
                [KeyboardButton(text="/manage - 👤 مدیریت پارتنر")],
                [KeyboardButton(text="/status - 📜 مشاهده وضعیت")],
            ],
            resize_keyboard=True
        )
        await callback.message.answer("🎮 منوی اصلی:", reply_markup=menu)
    else:
        await callback.answer("❌ شما هنوز عضو کانال نشده‌اید", show_alert=True)

@dp.message(Command("status"))
async def show_status_cmd(message: types.Message):
    """ نمایش وضعیت کاربر """
    # بررسی عضویت کاربر در کانال
    if not await check_user_subscription(message):
        return
    
    user_id = message.from_user.id
    cursor.execute("SELECT unique_code, partner_id FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()
    
    if not user_data:
        await message.answer("⚠️ اطلاعات شما در سیستم یافت نشد. لطفاً دوباره /start را ارسال کنید.")
        return
    
    unique_code, partner_id = user_data
    
    # بررسی تعداد چالش های پاسخ داده شده
    cursor.execute("SELECT COUNT(*) FROM questions WHERE user_id = ? AND answer IS NOT NULL", (user_id,))
    answered_challenges = cursor.fetchone()[0]
    
    partner_status = "❌ هیچ پارتنری ندارید." if not partner_id else f"✅ متصل به پارتنر: [{partner_id}](tg://user?id={partner_id})"
    
    await message.answer(
        f"📊 **وضعیت شما:**\n\n"
        f"🆔 آیدی شما: `{user_id}`\n"
        f"🔑 کد اختصاصی: `{unique_code}`\n"
        f"🎯 تعداد چالش‌های پاسخ داده شده: {answered_challenges}\n\n"
        f"{partner_status}",
        parse_mode="Markdown"
    )

@dp.message()
async def process_message(message: types.Message):
    """ مدیریت پیام‌ها و پاسخ‌های کاربران """
    user_id = message.from_user.id
    
    # بررسی عضویت کاربر در کانال
    is_subscribed = await check_subscription(user_id)
    if not is_subscribed:
        subscription_keyboard = get_subscription_keyboard()
        await message.answer(
            f"⚠️ برای استفاده از ربات، ابتدا باید در کانال {CHANNEL_TITLE} عضو شوید.",
            reply_markup=subscription_keyboard
        )
        return
    
    # بررسی وضعیت کاربر
    cursor.execute("SELECT partner_id, waiting_for_code FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()
    
    if not user_data:
        await message.answer("⚠️ اطلاعات شما در سیستم یافت نشد. لطفاً دوباره /start را ارسال کنید.")
        return
    
    partner_id, waiting_for_code = user_data
    
    # اگر کاربر منتظر ورود کد است
    if waiting_for_code == 1:
        code = message.text.strip() if message.text else None
        
        if code:
            cursor.execute("SELECT user_id FROM users WHERE unique_code=?", (code,))
            potential_partner = cursor.fetchone()
            
            if potential_partner:
                await process_partner_connection(message, potential_partner[0])
            else:
                await message.answer("❌ کد وارد شده صحیح نیست. لطفاً دوباره تلاش کنید یا /start را ارسال کنید.")
            
            # خروج از حالت انتظار برای کد
            cursor.execute("UPDATE users SET waiting_for_code = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
        else:
            await message.answer("⚠️ لطفاً یک کد معتبر وارد کنید یا /start را ارسال کنید.")
        
        return
    
    # بررسی متن دکمه‌ها
    if message.text:
        if message.text.startswith("/connect") or "اتصال به پارتنر" in message.text:
            await connect_partner_cmd(message)
            return
        elif message.text.startswith("/manage") or "مدیریت پارتنر" in message.text:
            await manage_partner_cmd(message)
            return
        elif message.text.startswith("/status") or "مشاهده وضعیت" in message.text:
            await show_status_cmd(message)
            return
    
    # بررسی اینکه آیا کاربر هنوز پارتنر ندارد
    if not partner_id:
        await message.answer("❌ شما هنوز به پارتنری متصل نشده‌اید. لطفاً ابتدا با استفاده از دستور /connect یا دکمه مربوطه به یک پارتنر متصل شوید.")
        return
    
    # بررسی اینکه آیا این پیام پاسخ به سوال است یا چت عادی
    cursor.execute("SELECT id, question FROM questions WHERE user_id = ? AND partner_id = ? AND answer IS NULL", (user_id, partner_id))
    question_data = cursor.fetchone()
    
    if question_data:
        question_id, question_text = question_data
        answer_text = None
        media_type = None
        media_id = None
        
        # استخراج متن پاسخ از انواع مختلف پیام
        if message.text:
            answer_text = message.text
        elif message.caption:
            answer_text = message.caption
            
        if message.photo:
            media_type = "photo"
            media_id = message.photo[-1].file_id
        elif message.video:
            media_type = "video"
            media_id = message.video.file_id
        elif message.voice:
            media_type = "voice"
            media_id = message.voice.file_id
        elif message.video_note:
            media_type = "video_note"
            media_id = message.video_note.file_id
        
        # ذخیره پاسخ در دیتابیس
        cursor.execute("UPDATE questions SET answer = ? WHERE id = ?", (answer_text, question_id))
        conn.commit()
        
        await message.answer("✅ پاسخ شما به چالش ذخیره شد.")
        
        # بررسی آیا پارتنر هم پاسخ داده است
        cursor.execute("SELECT answer FROM questions WHERE user_id = ? AND partner_id = ? AND question = ?", 
                       (partner_id, user_id, question_text))
        partner_answer = cursor.fetchone()
        
        if partner_answer and partner_answer[0]:  # اگر پارتنر پاسخ داده باشد
            # ارسال پاسخ پارتنر به کاربر
            await bot.send_message(user_id, 
                                  f"🎯 هر دو نفر به چالش پاسخ دادید! پاسخ پارتنر شما:\n\n"
                                  f"❓ سوال: {question_text}\n"
                                  f"💬 پاسخ پارتنر: {partner_answer[0]}")
            
            # ارسال پاسخ کاربر به پارتنر
            await bot.send_message(partner_id, 
                                 f"🎯 هر دو نفر به چالش پاسخ دادید! پاسخ پارتنر شما:\n\n"
                                 f"❓ سوال: {question_text}\n"
                                 f"💬 پاسخ پارتنر: {answer_text}")
            
            # اگر مدیا وجود دارد، آن را نیز برای پارتنر ارسال کن
            if media_type and media_id:
                if media_type == "photo":
                    await bot.send_photo(partner_id, media_id, caption="📷 تصویر پاسخ پارتنر شما")
                elif media_type == "video":
                    await bot.send_video(partner_id, media_id, caption="🎬 ویدیوی پاسخ پارتنر شما")
                elif media_type == "voice":
                    await bot.send_voice(partner_id, media_id, caption="🎤 صدای پاسخ پارتنر شما")
                elif media_type == "video_note":
                    await bot.send_video_note(partner_id, media_id)
        else:
            # اطلاع به پارتنر که یک پاسخ دریافت شده است
            await bot.send_message(partner_id, 
                                 f"⚠️ پارتنر شما به چالش پاسخ داده است.\n\n"
                                 f"❓ سوال: {question_text}\n\n"
                                 f"✏️ شما هنوز پاسخ نداده‌اید. پاسخ دهید تا پاسخ پارتنرتان را ببینید.")
                
        # اطلاع به ادمین
        admin_notification = f"🔔 کاربر {user_id} به چالش پاسخ داد:\n"
        admin_notification += f"سوال: {question_text}\n"
        admin_notification += f"پاسخ: {answer_text or 'بدون متن'}"
        
        await bot.send_message(ADMIN_ID, admin_notification)
        
        # ارسال مدیا به ادمین اگر وجود داشته باشد
        if media_type and media_id:
            admin_media_caption = f"🔔 مدیای پاسخ چالش از کاربر {user_id} به سوال: {question_text}"
            
            if media_type == "photo":
                await bot.send_photo(ADMIN_ID, media_id, caption=admin_media_caption)
            elif media_type == "video":
                await bot.send_video(ADMIN_ID, media_id, caption=admin_media_caption)
            elif media_type == "voice":
                await bot.send_voice(ADMIN_ID, media_id, caption=admin_media_caption)
            elif media_type == "video_note":
                await bot.send_message(ADMIN_ID, f"🔔 کاربر {user_id} یک ویدیو مسیج در پاسخ به چالش ارسال کرد")
                await bot.send_video_note(ADMIN_ID, media_id)
        
        return
    
    # پردازش پیام عادی
    message_text = None
    media_type = None
    media_id = None
    
    if message.text:
        message_text = message.text
    elif message.caption:
        message_text = message.caption
    
    if message.photo:
        media_type = "photo"
        media_id = message.photo[-1].file_id
    elif message.video:
        media_type = "video"
        media_id = message.video.file_id
    elif message.voice:
        media_type = "voice"
        media_id = message.voice.file_id
    elif message.video_note:
        media_type = "video_note"
        media_id = message.video_note.file_id
    elif message.sticker:
        media_type = "sticker"
        media_id = message.sticker.file_id
    
    # ذخیره پیام در دیتابیس
    cursor.execute(
        "INSERT INTO messages (sender_id, receiver_id, message, media_type, media_id) VALUES (?, ?, ?, ?, ?)",
        (user_id, partner_id, message_text, media_type, media_id)
    )
    conn.commit()
    
    # ارسال پیام به پارتنر
    if message_text:
        await bot.send_message(partner_id, f"💬 **پیام جدید از پارتنرت:**\n{message_text}")
    
    # ارسال مدیا به پارتنر
    if media_type and media_id:
        caption = "📩 مدیا از طرف پارتنر شما"
        if message_text:
            caption = message_text
            
        if media_type == "photo":
            await bot.send_photo(partner_id, media_id, caption=caption)
        elif media_type == "video":
            await bot.send_video(partner_id, media_id, caption=caption)
        elif media_type == "voice":
            await bot.send_voice(partner_id, media_id, caption=caption)
        elif media_type == "video_note":
            await bot.send_video_note(partner_id, media_id)
        elif media_type == "sticker":
            await bot.send_sticker(partner_id, media_id)
    
    # ارسال کپی پیام به ادمین
    admin_message = f"🔄 پیام از کاربر {user_id} به {partner_id}:"
    if message_text:
        admin_message += f"\n{message_text}"
    else:
        admin_message += f"\n[{media_type}]"
    
    await bot.send_message(ADMIN_ID, admin_message)
    
    # ارسال مدیا به ادمین
    if media_type and media_id:
        admin_media_caption = f"🔄 مدیا از کاربر {user_id} به کاربر {partner_id}"
        if message_text:
            admin_media_caption += f"\nپیام: {message_text}"
            
        if media_type == "photo":
            await bot.send_photo(ADMIN_ID, media_id, caption=admin_media_caption)
        elif media_type == "video":
            await bot.send_video(ADMIN_ID, media_id, caption=admin_media_caption)
        elif media_type == "voice":
            await bot.send_voice(ADMIN_ID, media_id, caption=admin_media_caption)
        elif media_type == "video_note":
            await bot.send_message(ADMIN_ID, f"🔄 کاربر {user_id} یک ویدیو مسیج برای کاربر {partner_id} ارسال کرد")
            await bot.send_video_note(ADMIN_ID, media_id)
        elif media_type == "sticker":
            await bot.send_message(ADMIN_ID, f"🔄 کاربر {user_id} یک استیکر برای کاربر {partner_id} ارسال کرد")
            await bot.send_sticker(ADMIN_ID, media_id)

async def process_partner_connection(message: types.Message, partner_id: int):
    """ اتصال دو کاربر به یکدیگر """
    user_id = message.from_user.id
    
    # بررسی اینکه آیا خود کاربر است
    if user_id == partner_id:
        await message.answer("❌ شما نمی‌توانید به خودتان متصل شوید!")
        return
    
    # بررسی اینکه آیا پارتنر قبلاً به کسی متصل است
    cursor.execute("SELECT partner_id FROM users WHERE user_id=?", (partner_id,))
    partner_data = cursor.fetchone()
    
    if partner_data and partner_data[0]:
        await message.answer("❌ کاربر مورد نظر قبلاً به پارتنر دیگری متصل شده است.")
        return
    
    # بررسی اینکه آیا کاربر قبلاً به کسی متصل است
    cursor.execute("SELECT partner_id FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()
    
    if user_data and user_data[0]:
        await message.answer("❌ شما قبلاً به پارتنر دیگری متصل شده‌اید. ابتدا ارتباط فعلی را قطع کنید.")
        return

    # اتصال دو طرفه
    cursor.execute("UPDATE users SET partner_id = ? WHERE user_id = ?", (partner_id, user_id))
    cursor.execute("UPDATE users SET partner_id = ? WHERE user_id = ?", (user_id, partner_id))
    conn.commit()

    await message.answer("✅ شما و پارتنرتان با موفقیت متصل شدید!")
    await bot.send_message(partner_id, f"✅ کاربر {user_id} با استفاده از کد شما متصل شد!")

    # اطلاع به ادمین
    await bot.send_message(
        ADMIN_ID, 
        f"🔗 اتصال جدید: کاربر {user_id} به کاربر {partner_id} متصل شد."
    )
    
    # ارسال اولین سوال چالشی
    await send_question(user_id, partner_id)

async def main():
    # شروع تسک ارسال سوالات زمان‌بندی شده
    asyncio.create_task(scheduled_questions())
    
    # شروع پالسینگ ربات
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 
