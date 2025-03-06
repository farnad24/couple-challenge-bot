import logging
import sqlite3
import random
import asyncio
import time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import string

# 🔑 تنظیمات اصلی
TOKEN = "Robot Token"
ADMIN_ID = 227975536  # آیدی عددی مدیر
REQUIRED_CHANNEL = "@your_channel"  # آیدی کانال اجباری (مثال: @your_channel)
CHANNEL_TITLE = "کانال رسمی"  # عنوان کانال برای نمایش به کاربر
SUPPORT_CHAT_ID = ADMIN_ID  # آیدی چت پشتیبانی (فعلا همان ادمین)
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
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    unique_code TEXT UNIQUE,
    partner_id INTEGER DEFAULT NULL,
    waiting_for_code INTEGER DEFAULT 0,
    last_question_time INTEGER DEFAULT 0,
    waiting_for_support TEXT DEFAULT NULL
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    partner_id INTEGER,
    question TEXT,
    answer TEXT DEFAULT NULL,
    timestamp INTEGER DEFAULT NULL
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER,
    receiver_id INTEGER,
    message TEXT DEFAULT NULL,
    media_type TEXT DEFAULT NULL,
    media_id TEXT DEFAULT NULL
)''')

# بررسی وجود ستون timestamp در جدول questions
cursor.execute("PRAGMA table_info(questions)")
columns = [column[1] for column in cursor.fetchall()]

# اگر ستون timestamp وجود نداشت، آن را اضافه کن
if "timestamp" not in columns:
    cursor.execute("ALTER TABLE questions ADD COLUMN timestamp INTEGER DEFAULT NULL")
    
    # به‌روزرسانی رکوردهای موجود با زمان فعلی
    current_time = int(time.time())
    cursor.execute("UPDATE questions SET timestamp = ? WHERE timestamp IS NULL", (current_time,))
    conn.commit()

conn.commit()

# لیست سوالات چالشی برای زوج‌ها
questions = [
    # سوالات موجود
    "سه چیزی که دوست داری قبل از مرگت انجام بدی چیه؟",
    "اگر پول مشکل نبود، کجا زندگی می‌کردی؟",
    "اگه می‌تونستی هر چیزی رو در دنیا تغییر بدی، چی رو انتخاب می‌کردی؟",
    "اگه می‌تونستی با یه شخصیت مشهور شام بری، کی رو انتخاب می‌کردی؟",
    "اگه قرار بود فقط یک وسیله رو به یه جزیره متروک ببری، چی انتخاب می‌کردی؟",
    "جسورانه‌ترین کاری که تا حالا انجام دادی چی بوده؟",
    "بهترین روز زندگیت چطور می‌گذشت؟",
    "اگه می‌تونستی با هر کسی ملاقات کنی، کی رو انتخاب می‌کردی؟",
    "اگه یه میلیارد تومن بهت بدن، با اولین صد میلیونش چیکار می‌کنی؟",
    "خطرناک‌ترین کاری که حاضری انجام بدی چیه؟",
    "عمیق‌ترین ترسی که داری چیه و چرا؟",
    "چه احساسی رو سخت‌تر از همه می‌تونی ابراز کنی؟",
    "چه چیزی باعث میشه که احساس کنی دوست داشته نمیشی؟",
    "از چه چیزی بیشتر از همه خجالت می‌کشی؟",
    "چه چیزی باعث میشه نسبت به پارتنرت احساس ناامنی کنی؟",
    "چه موقع‌هایی احساس می‌کنی واقعاً زنده‌ای؟",
    "چیزی هست که دوست داشته باشی بیشتر از پارتنرت بشنوی؟",
    "اگه یکی از شما مجبور بشه از شهر دیگه‌ای کار کنه، چطور رابطه‌تون رو مدیریت می‌کنید؟",
    "بدترین دروغی که تا حالا به کسی گفتی چی بوده؟",
    "چه کتابی خوندی که زندگیت رو تغییر داده؟",
    "چه چیزهایی دوست داری تو زندگیت بیشتر داشته باشی؟",
    "مسئولیت مالی خونه به نظرت باید با کی باشه؟",
    "بزرگترین زخم روحی‌ای که داری چیه؟",
    "گرمترین آغوش رو از چه کسی دریافت کردی؟",
    "چه مهارت‌هایی دوست داری به بچه‌هات یاد بدی؟",
    "در یک کلمه، عشق برات چه معنایی داره؟",
    "چیزهایی که تو رابطه آزارت میده رو معمولاً میگی یا نگه میداری؟",
    "چه کسی بیشترین تاثیر رو روی شخصیتت گذاشته؟",
    "دوست داری پارتنرت چطوری ابراز عشق و علاقه کنه؟",
    
    # سوالات عمومی رابطه
    "اگر یک آرزوی غیرممکن داشتی، چی بود؟",
    "بزرگترین ترس زندگیت چیه؟",
    "بهترین خاطره‌ای که با پارتنرت داری چیه؟",
    "اگر می‌تونستی یک چیز رو در زندگیت تغییر بدی، چی بود؟",
    "چه چیزی در رابطه‌مون بیشتر از همه تو رو خوشحال می‌کنه؟",
    "بزرگترین آرزوت برای آینده‌مون چیه؟",
    "اولین باری که فهمیدی عاشق پارتنرت شدی، کی بود؟",
    "تا حالا فکر کردی رابطه‌تون به پایان برسه؟ چرا؟",
    "اگه یک روز از رابطه‌تون مونده بود، چطور می‌گذروندیش؟",
    "بزرگترین دعوایی که با هم داشتید چی بود؟",
    "اگه بتونی یکی از صفات منفی پارتنرت رو تغییر بدی، کدوم رو انتخاب می‌کنی؟",
    "اولین چیزی که در مورد پارتنرت توجهت رو جلب کرد چی بود؟",
    "تا حالا به پارتنرت دروغ گفتی؟ در چه موردی؟",
    "تو آینده دوست داری چند تا بچه داشته باشی؟",
    "اگه پارتنرت بخواد به شهر دیگه‌ای نقل مکان کنه، چیکار می‌کنی؟",
    "کدوم عادت پارتنرت بیشتر اذیتت می‌کنه؟",
    "چیزی هست که دوست داری به پارتنرت بگی ولی هنوز نگفتی؟",
    "تا حالا پارتنرت رو دوست نداشتی؟ چه زمانی؟",
    "بیشترین مدت زمان قهرت با پارتنرت چقدر بوده؟",
    "اگه ازت خواستگاری بشه، چطور دوست داری باشه؟",
    "اگه پارتنرت به یک سفر طولانی کاری بره، چقدر دلتنگش میشی؟",
    "اگه امروز آخرین روز زندگیت بود، آخرین حرفت به پارتنرت چی بود؟",
    "چقدر حاضری برای خوشحالی پارتنرت از خودت بگذری؟",
    "چه چیزی باعث میشه تو این رابطه احساس امنیت کنی؟",
    "کی و کجا بهترین لحظات رابطه‌تون رو تجربه کردید؟",
    "چه چیزی تو رابطه‌تون هست که از حرف زدن در موردش طفره میری؟",
    
    # سوالات جنسی و صمیمانه (صریح‌تر)
    "بهترین سکس زندگیت کی و کجا بود؟",
    "اگر بخوای یک فانتزی جنسی رو با پارتنرت تجربه کنی، چی هست؟",
    "دوست داری رابطه جنسی بعدیتون کجا باشه؟",
    "دوست داری پارتنرت در رابطه جنسی خشن باشه یا ملایم؟",
    "آیا تا حالا به فکر رابطه سه نفره افتادی؟ نظرت چیه؟",
    "دوست داری پارتنرت موقع رابطه چه حرف‌هایی بهت بزنه؟",
    "به پارتنرت اعتراف کن که چه چیزی در بدنش بیشتر از همه تحریکت میکنه؟",
    "دوست داری پارتنرت موقع رابطه جنسی چه لباسی بپوشه؟",
    "جذاب‌ترین خاطره جنسی که با پارتنرت داشتی چی بوده؟",
    "اگر ۲۴ ساعت هر کاری میتونستی با بدن پارتنرت بکنی، چیکار میکردی؟",
    "رابطه دهانی برات مهمه؟ چقدر؟",
    "تا حالا به رابطه جنسی با فردی غیر از پارتنرت فکر کردی؟",
    "بهترین ارگاسمی که تجربه کردی چطور بود؟",
    "موقع خودارضایی به چی فکر میکنی؟",
    "تمایل به استفاده از اسباب‌بازی جنسی داری؟",
    "هر چند وقت یکبار نیاز جنسی داری؟",
    "دوست داری پارتنرت چه مدل موهای زهار داشته باشه؟",
    "غیر از اندام تناسلی، کدوم قسمت بدنت حساس‌ترین نقطه برای تحریک شدنه؟",
    "اگر پارتنرت بخواد یه عکس سکسی ازت داشته باشه، قبول میکنی؟",
    "سکس تحت تاثیر الکل یا مواد مخدر رو امتحان کردی؟ نظرت چیه؟",
    "دوست داری پارتنرت روی کدوم قسمت بدنت بیشتر تمرکز کنه؟",
    "اولین تجربه جنسی‌ات چطور بود؟",
    "به نظرت مهم‌ترین چیز در رابطه جنسی چیه؟",
    "اگر قرار باشه یک پوزیشن جدید با پارتنرت امتحان کنی، چی هست؟",
    "از قبل برای رابطه جنسی برنامه‌ریزی میکنی یا ترجیح میدی خودبه‌خود اتفاق بیفته؟",
    "کسی هست که بخوای پارتنرت ندونه بهش جذب جنسی داری؟",
    "بزرگترین آرزوی جنسی‌ات چیه؟",
    "تا حالا خواب جنسی دیدی که بعد از بیدار شدن خجالت کشیده باشی؟",
    "یه فانتزی جنسی خاص داری که تا حالا به کسی نگفته باشی؟",
    "آیا به رابطه باز (داشتن رابطه با افراد دیگر با توافق طرفین) فکر کردی؟",
    "چند سالت بود که اولین بار انگیزش جنسی رو تجربه کردی؟",
    "تا حالا رابطه جنسی تو مکان عمومی داشتی؟ یا دوست داری امتحان کنی؟",
    "اگه پارتنرت بخواد یه رابطه مقعدی داشته باشه، قبول می‌کنی؟",
    "جذاب‌ترین چیز در رابطه جنسی برات چیه؟",
    "تو رابطه جنسی ترجیح میدی تسلیم باشی یا مسلط؟",
    "دوست داری پارتنرت قبل از رابطه چه کاری انجام بده؟",
    "خاص‌ترین مکانی که دوست داری رابطه جنسی داشته باشی کجاست؟",
    "چیزی هست که تو رابطه جنسی حاضر نباشی انجام بدی؟",
    "دوست داری رابطه جنسی چقدر طول بکشه؟",
    "چه کلمات یا جملاتی دوست داری موقع رابطه از پارتنرت بشنوی؟",
    "تا حالا تو رابطه جنسی به چیزی وانمود کردی که واقعیت نداشته؟",
    "چقدر برات مهمه که پارتنرت از نظر جنسی فقط با تو باشه؟",
    "چیزی هست که پارتنرت تو رابطه جنسی انجام بده و خیلی دوستش داشته باشی؟",
    "چیزی هست که پارتنرت تو رابطه جنسی انجام بده و اصلا خوشت نیاد؟",
    "دوست داری پارتنرت موهات رو بکشه؟",
    "آیا دوست داری پارتنرت روت اسپنک بزنه؟",
    "دوست داری موقع رابطه جنسی از آینه استفاده کنی و خودتون رو ببینی؟",
    "تا حالا به فکر فیلم گرفتن از رابطه جنسی‌تون افتادی؟",
    "دوست داری رابطه دهانی رو دریافت کنی یا انجام بدی؟",
    "دوست داری پارتنرت چه عطری بزنه که تحریکت کنه؟",
    "چه لباس زیری دوست داری پارتنرت بپوشه؟",
    "بدن پارتنرت رو با چه چیزی دوست داری تزیین کنی؟ (شکلات، خامه، و...)",
    "دوست داری چشمات بسته باشه یا پارتنرت رو ببینی؟",
    "اگه پارتنرت بخواد یک نقش‌بازی جنسی انجام بده، چه نقشی دوست داری بازی کنه؟",
    "دوست داری از وسایل بانداژ استفاده کنی؟",
    "اگه اجازه داشته باشی فقط یک قسمت از بدن پارتنرت رو لمس کنی، کدوم قسمت رو انتخاب می‌کنی؟",
    "بیشتر ترجیح میدی زود ارضا بشی یا رابطه طولانی‌مدت داشته باشی؟",
    "اگه فقط یک پوزیشن می‌تونستی تا آخر عمر داشته باشی، کدوم رو انتخاب می‌کردی؟",
    "دوست داری تو چه شرایطی ارضا بشی؟",
    "چه فانتزی‌ای داری که خجالت می‌کشی به پارتنرت بگی؟",
    "دوست داری رابطه جنسی‌تون چقدر صدا داشته باشه؟",
    "دوست داری تو حمام یا وان رابطه داشته باشی؟",
    "از اینکه پارتنرت بدن برهنه‌ات رو ببینه چه احساسی داری؟",
    "تا حالا شده موقع رابطه به پارتنرت فکر نکنی؟",
    "خودارضایی رو چند بار در هفته انجام میدی؟",
    "چه کار غیرمعمولی دوست داری پارتنرت در رابطه جنسی انجام بده؟",
    "دوست داری با پارتنرت پورن ببینی؟",
    "بهترین زمان روز برای رابطه جنسی از نظرت چه زمانیه؟",
    "تا حالا بعد از رابطه جنسی پشیمون شدی؟",
    "بهترین مکان بدنت برای بوسیدن کجاست؟",
    "بعد از رابطه جنسی دوست داری چیکار کنی؟",
    "دوست داری لباس خاصی موقع رابطه بپوشی؟",
    "دوست داری روی چه سطحی غیر از تخت رابطه داشته باشی؟",
    "ارگاسم مصنوعی داشتی یا وانمود کردی؟",
    "اگر می‌تونستی آرزو کنی پارتنرت یک مهارت جنسی جدید یاد بگیره، چی رو انتخاب می‌کردی؟",
    
    # سوالات متفرقه
    "بوسه یا آغوش؟",
    "دوست داری چه هدیه‌ای از پارتنرت بگیری؟",
    "دوست داری با همدیگه به کجا سفر کنین؟",
    "وقتی عصبانی هستی دوست داری تنها باشی یا درموردش با هم حرف بزنید؟",
    "چیزی هست که دلت بخواد به پارتنرت بگی و تا حالا نگفتی؟",
    "فیلم دیدن توی خونه یا سینما؟",
    "اولین چیزی که از پارتنرت به نظرت جذاب اومد چی بود؟",
    "نظرت درمورد به فرزندی گرفتن یه بچه بی‌سرپرست چیه؟",
    "از نظر تو مهم‌ترین مناسبت (تولد، سالگرد ازدواج، ولنتاین و...) چیه؟",
    "بزرگترین نقطه ضعف پارتنرت از نظر تو چیه؟",
    "چی در مورد بچگی‌هات وجود داره که دلت بخواد به پارتنرت بگی؟",
    "با یک کلمه پارتنرت رو توصیف کن",
    "لوکیشن یا جای خاصی هست که دوست داشته باشی به پارتنرت نشون بدی؟",
    "از بین دوستان پارتنرت از چه کسی خوشت نمیاد و چرا؟",
    "مکان ایده‌آلت برای زندگی با همدیگه کجاست؟",
    "اگه پارتنرت چه کاری رو انجام بده اصلا نمی‌تونی ببخشیش؟",
    "چه هدف مشترکی برای ۵ سال آینده تو ذهنته که دوست داری با همدیگه بهش برسید؟",
    "بهترین ویژگی پارتنرت از نظر تو چیه؟",
    "بنظرت ۱۰ سال دیگه وضعیت رابطتون به چه صورته؟",
    "از چه خوش‌گذرونی‌های کوچیکی بیشترین لذت رو می‌بری؟",
    "چه زمانی احساس می‌کنی واقعا خودت هستی؟",
    "به چه چیزی در مورد پارتنرت افتخار می‌کنی؟",
    "آخرین باری که گریه کردی کی بوده؟",
    "کدوم عادت رو از بچگی تا الان داری؟",
    "چه سرگرمی یا فعالیت‌هایی هست که دوست داری با همدیگه انجام بدید؟",
    "بنظرت چطوری می‌تونی پارتنرت رو خوشبخت کنی؟",
    "چی باعث میشه حس فوق‌العاده‌ای به خودت پیدا کنی؟",
    "بنظرت بزرگترین نقطه قوت رابطتون چیه؟",
    "دوست داری وقتی بازنشسته شدید، کجا زندگی کنید؟",
    "بنظرت وقتی پارتنرت پیر بشه رو اعصاب‌ترین اخلاقش چیه؟",
    "نظرت در مورد اینکه گاهی پارتنرت به تنهایی یا با دوستانش بره سفر چیه؟",
    "اگه بتونی یه چیزی رو در رابطه دونفرتون تغییر بدی اون چیه؟",
    "چه چیزی رو در خودت دوست نداری و دلت میخواد تغییرش بدی؟",
    "بوسه از پیشونی یا گونه؟",
    "شادترین لحظه‌ای که تا الان با هم داشتید کی بوده؟",
    "بزرگ‌ترین چالشی که باهم تا الان داشتید چیه؟",
    "وقتی که ناراحتی پارتنرت چه کاری انجام بده حالت بهتر میشه؟",
    "یه عمارت بزرگ خارج از شهر یا یه آپارتمان کوچیک داخل شهر؟",
    "بوسه زیر بارون یا لب دریا؟",
    "بنظرت بزرگ‌ترین نقطه ضعف رابطتون چیه؟",
    "به چه چیزی در مورد خودت افتخار می‌کنی؟",
    "حاضری در مکان‌های عمومی هم رو ببوسید؟",
    "ترجیح میدی چه کاری رو به جای پارتنرت با دوستات انجام بدی؟",
    "عشقبازی یا ارگاسم؟",
    "نظرت در مورد فردیت در رابطه و گاهی تنها بودن و داشتن حریم شخصی در عین داشتن تعهد چیه؟",
    "دست‌هاش یا چشم‌هاش؟",
    "بنظرت وقتی ناراحتی پارتنرت باید خودش بفهمه یا خودت باید بهش بگی چی ناراحتت کرده؟",
    "سه تا چیزی که دوست داری در مورد پارتنرت تغییر بدی چیه؟",
    "با شنیدن کدوم آهنگ یاد پارتنرت میفتی؟",
    "از انجام چه کاری تو زندگیت پشیمان هستی؟",
    "کدوم ویژگی ظاهری پارتنرت رو دوست داری؟",
    "از کدوم لباس پارتنرت بیشتر خوشت میاد؟",
    "به خونسردی پارتنرت از ۱ تا ۱۰ یک امتیاز بده",
    "اگه برای یک روز نامرئی بودی، چیکار می‌کردی؟",
    "اگه می‌تونستی یه ابرقدرت داشته باشی، چی انتخاب می‌کردی؟",
    "اگه دنیا فردا تموم می‌شد، آخرین کاری که با پارتنرت می‌کردی چی بود؟",
    "جسورانه‌ترین کاری که دوست داری با پارتنرت انجام بدی چیه؟",
    "دوست داری چه ماجراجویی رو با هم تجربه کنید؟",
    
    # سوالات عمیق‌تر رابطه
    "چه مسئله‌ای در رابطه‌مون هست که از حرف زدن در موردش طفره میری؟",
    "در یک سال آینده، خودت رو کجا می‌بینی؟ ما رو کجا می‌بینی؟",
    "تا حالا احساس کردی که می‌خوای از این رابطه بیرون بری؟ چرا؟",
    "چه چیزی در رابطه‌مون بیشتر از همه تو رو آزار میده؟",
    "اگر می‌تونستی یکی از ترس‌هات رو با من به اشتراک بذاری، چی میگفتی؟",
    "کدوم تصمیم مشترکمون فکر می‌کنی اشتباه بوده؟",
    "چه چیزی در مورد من هست که هنوز نمی‌دونی ولی دوست داری بدونی؟",
    "بزرگترین دعوایی که با هم داشتیم چی بود؟ چطور می‌تونستیم بهترش کنیم؟",
    "تا حالا به من دروغ گفتی؟ چرا؟",
    "چیزی هست که من فکر کنم دوست داری، ولی در واقع اصلاً دوست نداشته باشی؟",
    "از چه چیزی در رابطه‌مون پشیمونی؟",
    "کدوم عادت‌هام بیشتر از همه اذیتت می‌کنه؟",
    "چه چیزی باعث میشه فکر کنی که ما برای هم مناسب هستیم؟",
    "چیزی هست که دوست داشته باشی در موردش با من صحبت کنی، ولی نتونستی؟",
    "اگر امروز آخرین روز زندگیت بود، چه حرفی به من می‌زدی؟",
    "وقتی عصبانی میشی، ترجیح میدی تنها باشی یا با من حرف بزنی؟",
    "تا حالا از من ناامید شدی؟ کِی و چرا؟",
    "چطور می‌تونیم بهتر با هم ارتباط برقرار کنیم؟",
    
    # سوالات درباره آینده
    "خودت رو تا ۱۰ سال آینده کجا می‌بینی؟",
    "دوست داری چند تا بچه داشته باشی؟",
    "به ازدواج با من فکر می‌کنی؟",
    "دوست داری کجا زندگی کنیم؟",
    "اگر قرار باشه با هم ازدواج کنیم، عروسی ایده‌آلت چطوریه؟",
    "بزرگترین هدفت برای ۵ سال آینده چیه؟",
    "تو آینده، دوست داری چه سبک زندگی‌ای داشته باشیم؟",
    "اگر روزی بخوایم با هم زندگی کنیم، کدوم یکی از عادت‌هات ممکنه منو اذیت کنه؟",
    "اگر من شغلی پیدا کنم که مجبور بشم به شهر دیگه‌ای برم، تو چیکار می‌کنی؟",
    "بزرگترین ترست در مورد تشکیل خانواده چیه؟",
    "اگر یکی از ما بیمار بشه، چطور با این موضوع کنار میای؟",
    "فکر می‌کنی تو آینده باید مسئولیت مالی خونه با کی باشه؟",
    "اگه بچه‌دار بشیم، چه ارزش‌هایی می‌خوای بهشون یاد بدی؟",
    "تو زندگی مشترک، انتظار داری وظایف خونه چطور تقسیم بشه؟",
    "اگر پدر و مادرت نیاز به مراقبت داشته باشن، انتظار داری چیکار کنیم؟",
    "تمایل داری کدوم سنت‌های خانوادگیت رو ادامه بدی؟",
    "بزرگترین هدفت برای رابطه‌مون چیه؟",
    "در مورد پس‌انداز و خرج کردن پول چه نظری داری؟",
    "دوست داری پیر شدنمون کنار هم چطوری باشه؟",
    "اگر یکی از ما فرصت شغلی خوبی پیدا کنه که باعث دوری ما بشه، تصمیمت چیه؟",
    
    # سوالات صمیمانه و جنسی
    "دوست داری بیشتر چه کاری رو با هم در رابطه امتحان کنیم؟",
    "جذاب‌ترین چیز در مورد من از نظر جسمی چیه؟",
    "فانتزی جنسی که دوست داری با من تجربه کنی چیه؟",
    "چیزی هست که من در رابطه جنسی انجام میدم و خیلی دوست داری؟",
    "تا حالا در حین رابطه با من به کس دیگه‌ای فکر کردی؟",
    "دوست داری رابطه‌مون رو چطوری هیجان‌انگیزتر کنیم؟",
    "کدوم قسمت بدنت دوست داری بیشتر لمس بشه؟",
    "جای خاصی هست که دوست داشته باشی رابطه داشته باشیم؟",
    "چیزی هست که دوست داشته باشی در رابطه امتحان کنی ولی روت نشده بگی؟",
    "اولین باری که با من رابطه داشتی، چه حسی داشتی؟",
    "از نظر تو بهترین رابطه‌ای که با هم داشتیم کی بوده؟",
    "از چیزی تو رابطه‌مون خجالت می‌کشی؟",
    "از نظر عاطفی، چه چیزی باعث میشه بیشتر تحریک بشی؟",
    "تا حالا بدون اینکه من بدونم، از چیزی تو رابطه‌مون لذت نبردی؟",
    "دوست داری چند وقت یکبار رابطه داشته باشیم؟",
    "چیزی هست که من در رابطه انجام میدم و تو خوشت نمیاد؟",
    "اگر بخوای یه چیز جدید تو رابطه امتحان کنی، چی انتخاب می‌کنی؟",
    "چه کلمات یا جمله‌هایی دوست داری موقع رابطه بشنوی؟",
    "دوست داری قبل از رابطه چیکار کنیم؟",
    "تا حالا تو رابطه‌مون به چیزی وانمود کردی؟",
    
    # سوالات شخصی و روانشناختی
    "کدوم تجربه زندگیت بیشتر از همه روت تأثیر گذاشته؟",
    "چه چیزی باعث میشه وقتی تنهایی گریه کنی؟",
    "سخت‌ترین چیزی که تا حالا به کسی گفتی چی بوده؟",
    "چه چیزی باعث میشه احساس شکست کنی؟",
    "آیا تا حالا فکر خودکشی داشتی؟",
    "آیا تا حالا به کسی خیانت کردی؟",
    "چه اتفاقی تو بچگی افتاده که هنوز روت تأثیر داره؟",
    "چه چیزی تو زندگی باعث میشه احساس گناه کنی؟",
    "از چه چیزی در خودت بیشتر از همه شرمنده‌ای؟",
    "اگه بتونی یه راز رو از من مخفی نگه داری، چی میبود؟",
    "چیزی هست که می‌خوای من در موردش بیشتر درکت کنم؟",
    "کدوم بخش از شخصیتت رو دوست نداری دیگران ببینن؟",
    "چه چیزی باعث میشه حس کنی که زندگیت ارزشمنده؟",
    "وقتی حالت بده، ترجیح میدی تنها باشی یا پیش من؟",
    "چه چیزی بیشتر از همه اعتماد به نفست رو از بین می‌بره؟",
    "چطور می‌تونم بهت کمک کنم وقتی حالت خوب نیست؟",
    "چه کاری می‌تونم انجام بدم که بیشتر احساس امنیت کنی؟",
    "بزرگترین نقطه ضعفت چیه؟",
    
    # سوالات در مورد گذشته
    "تلخ‌ترین خاطره زندگیت چیه؟",
    "رابطه قبلیت چطور تموم شد؟",
    "چیزی در گذشته‌ات هست که از من پنهان کرده باشی؟",
    "بدترین اشتباهی که تو زندگیت کردی چی بوده؟",
    "کسی تو گذشته هست که هنوز بهش فکر کنی؟",
    "چیزی در گذشته‌ات هست که آرزو کنی من هیچوقت نفهمم؟",
    "از کدوم بخش زندگیت بیشتر پشیمونی؟",
    "اگه می‌تونستی به گذشته برگردی، چه چیزی رو تغییر می‌دادی؟",
    "درباره رابطه‌های قبلیت چیزی هست که من ندونم؟",
    "کدوم خاطره از بچگیت بیشتر از همه دوست داری؟",
    "چیزی هست که تو گذشته اتفاق افتاده باشه و هنوز روت تأثیر داشته باشه؟",
    "چه دروغی به خانواده‌ات گفتی که هنوز نمی‌دونن حقیقت چیه؟",
    "تو گذشته کار بدی کردی که کسی نمی‌دونه؟",
    "تا حالا کسی رو واقعاً از ته دل بخشیدی؟",
    "بدترین شکستی که خوردی چی بوده؟",
    "اولین بوسه‌ات با کی بود؟",
    "اولین عشقت کی بود و چرا تموم شد؟",
    "چه اتفاقی تو زندگیت افتاده که باعث شده آدم متفاوتی بشی؟",
    "چه کسی در گذشته بیشترین آسیب رو بهت زده؟",
    "اگه بشه یه نفر از گذشته‌ات رو دوباره ببینی، کی رو انتخاب می‌کنی؟",
    
    # سوالات فانتزی و ماجراجویی
    "اگه برای یک روز نامرئی بودی، چیکار می‌کردی؟",
    "اگه می‌تونستی یه ابرقدرت داشته باشی، چی انتخاب می‌کردی؟",
    "اگه دنیا فردا تموم می‌شد، آخرین کاری که با من می‌کردی چی بود؟",
    "جسورانه‌ترین کاری که دوست داری با من انجام بدی چیه؟",
    "دوست داری کجا سفر کنیم که تا حالا نرفتیم؟",
    "دوست داری چه ماجراجویی رو با هم تجربه کنیم؟",
    "هیجان‌انگیزترین چیزی که دوست داری امتحان کنی چیه؟",
    "اگه می‌تونستی یه اختراع انجام بدی، چی اختراع می‌کردی؟",
    "اگه یه ماه وقت آزاد داشتی، چیکار می‌کردی؟",
    "اگه می‌تونستی توی هر دوره‌ای از تاریخ زندگی کنی، کدوم دوره رو انتخاب می‌کردی؟",
    
    # سوالات در مورد احساسات عمیق
    "چه موقع‌هایی بیشتر احساس تنهایی می‌کنی، حتی وقتی با منی؟",
    "آخرین باری که گریه کردی کِی بود و برای چی؟",
    "چطور می‌تونم وقتی ناراحتی، بهتر بهت کمک کنم؟",
    "چه کاری میتونم انجام بدم که بیشتر احساس کنی دوستت دارم؟",
    "بزرگترین نگرانیت در مورد آینده چیه؟",
    "چه موقع‌هایی احساس آرامش می‌کنی؟",
    "چه کاری من انجام میدم که ناخودآگاه اذیتت می‌کنه؟",
    "بزرگترین دلیلی که باعث میشه بخوای با من بمونی چیه؟",
    "از چه چیزهایی عمیقاً پشیمونی؟",
    "چه موقع‌هایی بیشتر از همه احساس می‌کنی که دوستت دارم؟",
    "چطور می‌تونم وقتی عصبانی هستی، بهتر کمکت کنم؟",
    "وقتی با منی، از چه چیزی می‌ترسی؟",
    "عمیق‌ترین آرزوت که تا حالا به کسی نگفتی چیه؟",
    
    # سوالات در مورد مسائل حساس
    "نظرت در مورد فرزندخوانده گرفتن چیه؟",
    "اگه یکی از ما نتونه بچه‌دار بشه، چه احساسی خواهی داشت؟",
    "به نظرت مسائل مالی باید بین زوج‌ها چطور مدیریت بشه؟",
    "در مورد روابط باز چه نظری داری؟",
    "اگه من به مشکل جدی سلامتی برخورد کنم، چه واکنشی نشون میدی؟",
    "نظرت در مورد مذهب و نقشش تو زندگی مشترکمون چیه؟",
    "اگه من تغییر عقیده سیاسی بدم، چه واکنشی نشون میدی؟",
    "چقدر برات مهمه که خانواده‌ات من رو تأیید کنن؟",
    "اگه من یه اشتباه بزرگ مرتکب بشم، چقدر می‌تونی من رو ببخشی؟",
    "اگه بخوام شغلم رو عوض کنم، چه واکنشی نشون میدی؟",
    "اگه من به افسردگی یا اضطراب مبتلا بشم، چطور کمکم می‌کنی؟",
    "در مورد مسائل حساس مثل طلاق چه نظری داری؟",
    "اگه یکی از نزدیکانت با من مشکل داشته باشه، چیکار می‌کنی؟",
    "آیا حاضری به خاطر من از برخی اهدافت دست بکشی؟",
    "آیا در مورد داشتن حساب بانکی مشترک احساس راحتی می‌کنی؟",
    "در مورد رابطه با جنس مخالف وقتی تو رابطه هستی چه نظری داری؟",
    "به نظرت صحبت با پارتنر قبلی قابل قبوله یا نه؟",
    "آیا حاضری بعد از ازدواج محل زندگیت رو تغییر بدی؟",
    "اگه من بخوام سبک زندگیم رو به طور اساسی تغییر بدم، چه واکنشی نشون میدی؟",
    
    # سوالات در مورد رشد شخصی
    "چه چیزی در مورد خودت دوست داری تغییر بدی؟",
    "بزرگترین هدفی که داری چیه و چطور می‌خوای بهش برسی؟",
    "چطور می‌تونم بهت کمک کنم تا به هدف‌هات برسی؟",
    "چه عادت بدی داری که می‌خوای ترکش کنی؟",
    "چطور می‌تونیم همدیگه رو برای رشد شخصی تشویق کنیم؟",
    "چه مهارت‌هایی دوست داری یاد بگیری؟",
    "به نظرت من چه چیزی می‌تونم از تو یاد بگیرم؟",
    "چه نقاط قوتی تو من می‌بینی که خودم متوجهشون نیستم؟",
    "کدوم یک از نقاط ضعفت رو دوست داری بهبود بدی؟",
    "چطور می‌تونم به موفقیت تو کمک کنم؟",
    "چه چیزی تو رابطه‌مون باعث میشه که رشد کنی؟",
    "چی باعث میشه احساس موفقیت کنی؟",
    "چطور می‌تونیم به عنوان یه زوج رشد کنیم؟",
    "بزرگترین درسی که از رابطه‌مون گرفتی چیه؟",
    "چه چیزی من می‌تونم از تو یاد بگیرم؟",
    "چطور می‌تونم در جهت رشد شخصیتت بهت کمک کنم؟",
    "از نظر معنوی، چه تجربه‌ای برات مهم بوده؟"
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

async def send_question(user_id, partner_id, force=False):
    """ ارسال سوال چالشی به دو پارتنر """
    
    try:
        # بررسی آیا کاربران سوال بی‌پاسخ دارند
        cursor.execute("SELECT id, question, timestamp FROM questions WHERE user_id = ? AND partner_id = ? AND answer IS NULL", (user_id, partner_id))
        unanswered_user = cursor.fetchone()
        
        cursor.execute("SELECT id, question, timestamp FROM questions WHERE user_id = ? AND partner_id = ? AND answer IS NULL", (partner_id, user_id))
        unanswered_partner = cursor.fetchone()
        
        # اگر کاربر اصلی سوال بی‌پاسخ دارد، از ارسال سوال جدید خودداری کن
        if unanswered_user or unanswered_partner:
            # فقط اطلاع‌رسانی کنیم که سوال بی‌پاسخ وجود دارد، بدون ارسال یادآوری
            # یادآوری‌ها توسط تابع send_reminders هر 5 ساعت ارسال می‌شوند
            return False
        
        # بررسی زمان آخرین سوال برای جلوگیری از ارسال سوال در کمتر از ۲ ساعت
        current_time = int(time.time())
        cursor.execute("SELECT last_question_time FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        last_question_time_user = 0 if result is None else result[0]
        
        two_hours_in_seconds = 7200  # 2 ساعت
        
        # اگر force=True باشد یا کمتر از دو ساعت از آخرین سوال گذشته، سوال جدید ارسال کن (به جز اولین سوال)
        if not force and last_question_time_user != 0 and (current_time - last_question_time_user) < two_hours_in_seconds:
            return False
            
        # اگر هر دو کاربر به سوالات قبلی پاسخ داده‌اند، سوال جدید ارسال کن
        question = random.choice(questions)
        
        # ایجاد سوال جدید برای هر دو کاربر
        cursor.execute("INSERT INTO questions (user_id, partner_id, question, timestamp) VALUES (?, ?, ?, ?)", (user_id, partner_id, question, current_time))
        question_id_1 = cursor.lastrowid
        
        cursor.execute("INSERT INTO questions (user_id, partner_id, question, timestamp) VALUES (?, ?, ?, ?)", (partner_id, user_id, question, current_time))
        question_id_2 = cursor.lastrowid
        
        # بروزرسانی زمان آخرین سوال برای هر دو کاربر
        cursor.execute("UPDATE users SET last_question_time = ? WHERE user_id = ?", (current_time, user_id))
        cursor.execute("UPDATE users SET last_question_time = ? WHERE user_id = ?", (current_time, partner_id))
        
        conn.commit()
        
        # ارسال سوال به کاربران
        try:
            await bot.send_message(user_id, f"💬 سوال جدید: {question}\n✏️ پاسخ خود را ارسال کنید.")
        except Exception as e:
            print(f"خطا در ارسال سوال به کاربر {user_id}: {e}")
        
        try:
            await bot.send_message(partner_id, f"💬 سوال جدید: {question}\n✏️ پاسخ خود را ارسال کنید.")
        except Exception as e:
            print(f"خطا در ارسال سوال به کاربر {partner_id}: {e}")
        
        # دریافت اطلاعات کاربران
        try:
            user_info = await bot.get_chat(user_id)
            user_identifier = user_info.username if user_info.username else user_info.first_name
        except:
            user_identifier = str(user_id)
            
        try:
            partner_info = await bot.get_chat(partner_id)
            partner_identifier = partner_info.username if partner_info.username else partner_info.first_name
        except:
            partner_identifier = str(partner_id)
        
        # ارسال پیام به ادمین با نام کاربری یا نام
        await bot.send_message(SUPPORT_CHAT_ID, f"🔔 سوال جدید به کاربران {user_identifier} و {partner_identifier} ارسال شد:\n{question}")
        
        return True
        
    except Exception as e:
        print(f"خطا در ارسال سوال: {e}")
        return False

async def scheduled_questions():
    """ ارسال سوال هر ۲ ساعت یک بار """
    while True:
        cursor.execute("SELECT user_id, partner_id, last_question_time FROM users WHERE partner_id IS NOT NULL")
        pairs = cursor.fetchall()

        # برای جلوگیری از ارسال سوال تکراری به زوج‌ها
        processed_pairs = set()
        current_time = int(time.time())
        two_hours_in_seconds = 7200  # 2 ساعت به ثانیه
        
        for user_id, partner_id, last_question_time in pairs:
            # ایجاد یک کلید منحصر به فرد برای هر زوج (با مرتب‌سازی شناسه‌ها)
            pair_key = tuple(sorted([user_id, partner_id]))
            
            # اگر این زوج قبلاً پردازش نشده‌اند و زمان کافی از آخرین سوال گذشته است
            if pair_key not in processed_pairs:
                # اگر هرگز سوال دریافت نکرده‌اند یا زمان کافی گذشته است
                if last_question_time == 0 or (current_time - last_question_time) >= two_hours_in_seconds:
                    await send_question(user_id, partner_id)
                processed_pairs.add(pair_key)

        await asyncio.sleep(300)  # بررسی هر ۵ دقیقه (برای کاهش مصرف منابع)

async def send_reminders():
    """ ارسال یادآوری هر ۵ ساعت برای سوالات بی‌پاسخ """
    while True:
        # ابتدا منتظر می‌مانیم تا 5 ساعت بگذرد
        await asyncio.sleep(18000)  # انتظار ۵ ساعت (18000 ثانیه)
        
        # سپس بررسی و ارسال یادآوری‌ها
        cursor.execute("SELECT q.id, q.user_id, q.partner_id, q.question, q.timestamp FROM questions q WHERE q.answer IS NULL")
        unanswered_questions = cursor.fetchall()
        current_time = int(time.time())
        five_hours_in_seconds = 18000  # 5 ساعت به ثانیه
        two_hours_in_seconds = 7200  # 2 ساعت به ثانیه
        
        for question_id, user_id, partner_id, question, timestamp in unanswered_questions:
            # بررسی آیا حداقل 2 ساعت از ایجاد سوال گذشته است
            if timestamp and (current_time - timestamp) >= two_hours_in_seconds:
                try:
                    await bot.send_message(user_id, f"🔔 یادآوری مجدد: شما هنوز به این سوال پاسخ نداده‌اید:\n\n{question}\n\n✏️ لطفاً پاسخ خود را ارسال کنید.")
                    # به‌روزرسانی زمان آخرین یادآوری
                    cursor.execute("UPDATE questions SET timestamp = ? WHERE id = ?", (current_time, question_id))
                    conn.commit()
                except Exception as e:
                    logging.error(f"خطا در ارسال یادآوری به کاربر {user_id}: {e}")
        
        await asyncio.sleep(18000)  # بررسی هر ۵ ساعت (18000 ثانیه)

@dp.message(Command("start"))
async def start(message: types.Message):
    """ ثبت‌نام و ایجاد کد اختصاصی """
    user_id = message.from_user.id
    is_new_user = False
    
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
        is_new_user = True
        unique_code = generate_unique_code()
        cursor.execute("INSERT INTO users (user_id, unique_code) VALUES (?, ?)", (user_id, unique_code))
        conn.commit()
        partner_id = None
    else:
        unique_code, partner_id = user_data

    partner_status = "❌ هیچ پارتنری ندارید." if not partner_id else f"✅ شما متصل هستید به: [{partner_id}](tg://user?id={partner_id})"

    # ایجاد دکمه‌های منوی اصلی با استفاده از تابع جدید
    if user_id == ADMIN_ID:
        menu = get_admin_menu_keyboard()
    else:
        menu = get_main_menu_keyboard()
    
    # تعریف دکمه‌های اینلاین
    inline_buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📨 ارسال دعوتنامه", callback_data="send_invitation")]
        ]
    )
    
    await message.answer(
        f"سلام {message.from_user.first_name}!\n\n🔑 **کد اختصاصی شما:** {unique_code}\n📨 این کد را برای پارتنرت بفرست تا متصل شود.\n\n{partner_status}\n\n"
        f"برای اتصال به پارتنر روی دکمه '/connect - 🔗 اتصال به پارتنر' کلیک کنید یا دستور /connect را ارسال کنید.",
        parse_mode="Markdown", reply_markup=menu
    )
    
    # ارسال پیام دوم با دکمه شیشه‌ای
    await message.answer("برای ارسال دعوتنامه به پارتنر، از دکمه زیر استفاده کنید:", reply_markup=inline_buttons)
    
    # اطلاع به ادمین فقط در صورت ثبت نام جدید
    if is_new_user:
        await bot.send_message(
            SUPPORT_CHAT_ID, 
            f"👤 کاربر جدید ثبت‌نام کرد:\nنام: {message.from_user.first_name}\nآیدی: {user_id}\nیوزرنیم: @{message.from_user.username or 'ندارد'}"
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
        # ایجاد دکمه برای قطع ارتباط
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ قطع ارتباط با پارتنر فعلی", callback_data="disconnect_partner")]
            ]
        )
        await message.answer("⚠️ شما در حال حاضر به یک پارتنر متصل هستید. برای اتصال به پارتنر جدید، ابتدا ارتباط فعلی را قطع کنید.", reply_markup=keyboard)
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
        
        # دریافت اطلاعات کاربران برای اطلاع‌رسانی بهتر
        try:
            user_info = await bot.get_chat(user_id)
            user_identifier = user_info.username if user_info.username else user_info.first_name
        except:
            user_identifier = str(user_id)
            
        try:
            partner_info = await bot.get_chat(partner_id)
            partner_identifier = partner_info.username if partner_info.username else partner_info.first_name
        except:
            partner_identifier = str(partner_id)
        
        # ایجاد دکمه برای اتصال به پارتنر جدید
        connect_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔗 اتصال به پارتنر جدید", callback_data="start_connect")]
            ]
        )
        
        await callback.message.edit_text("✅ ارتباط شما با پارتنر قطع شد.")
        await bot.send_message(user_id, "✅ اکنون می‌توانید با استفاده از دستور /connect به پارتنر جدیدی متصل شوید.", reply_markup=connect_keyboard)
        await bot.send_message(partner_id, f"⚠️ پارتنر شما ({user_identifier}) ارتباط را قطع کرد. شما می‌توانید با استفاده از دستور /connect به پارتنر جدیدی متصل شوید.")
        
        # اطلاع به ادمین
        await bot.send_message(SUPPORT_CHAT_ID, f"🔔 ارتباط بین {user_identifier} و {partner_identifier} قطع شد.")
    else:
        await callback.message.edit_text("⚠️ شما به پارتنری متصل نیستید.")
    
    await callback.answer()

@dp.callback_query(lambda c: c.data == "start_connect")
async def start_connect_callback(callback: types.CallbackQuery):
    """ شروع فرآیند اتصال به پارتنر جدید """
    user_id = callback.from_user.id
    
    # بررسی اینکه آیا کاربر پارتنر دارد
    cursor.execute("SELECT partner_id FROM users WHERE user_id=?", (user_id,))
    partner = cursor.fetchone()
    
    if partner and partner[0]:
        # ایجاد دکمه برای قطع ارتباط
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ قطع ارتباط با پارتنر فعلی", callback_data="disconnect_partner")]
            ]
        )
        await callback.message.edit_text("⚠️ شما در حال حاضر به یک پارتنر متصل هستید. برای اتصال به پارتنر جدید، ابتدا ارتباط فعلی را قطع کنید.", reply_markup=keyboard)
        await callback.answer()
        return
    
    # فعال کردن حالت انتظار برای کد
    cursor.execute("UPDATE users SET waiting_for_code = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    
    await callback.message.edit_text("🔍 لطفاً کد اختصاصی پارتنر خود را وارد کنید:")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "check_subscription")
async def check_subscription_callback(callback: types.CallbackQuery):
    """ بررسی مجدد عضویت کاربر در کانال """
    user_id = callback.from_user.id
    is_subscribed = await check_subscription(user_id)
    
    if is_subscribed:
        # بررسی و ایجاد کاربر اگر وجود نداشته باشد
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
        
        await callback.message.edit_text("✅ عضویت شما در کانال تایید شد. حالا می‌توانید از ربات استفاده کنید!")
        await callback.answer("✅ عضویت تایید شد")
        
        # ایجاد دکمه‌های منوی اصلی با استفاده از تابع جدید
        menu = get_main_menu_keyboard()
        
        # تعریف دکمه‌های اینلاین
        inline_buttons = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📨 ارسال دعوتنامه", callback_data="send_invitation")]
            ]
        )
        
        await callback.message.answer(
            f"سلام {callback.from_user.first_name}!\n\n🔑 **کد اختصاصی شما:** {unique_code}\n📨 این کد را برای پارتنرت بفرست تا متصل شود.\n\n{partner_status}\n\n"
            f"برای اتصال به پارتنر روی دکمه '/connect - 🔗 اتصال به پارتنر' کلیک کنید یا دستور /connect را ارسال کنید.",
            parse_mode="Markdown", reply_markup=menu
        )
        
        # ارسال پیام دوم با دکمه شیشه‌ای
        await callback.message.answer("برای ارسال دعوتنامه به پارتنر، از دکمه زیر استفاده کنید:", reply_markup=inline_buttons)
    else:
        await callback.answer("❌ شما هنوز عضو کانال نشده‌اید", show_alert=True)
        
        # ایجاد مجدد دکمه بررسی عضویت
        subscription_keyboard = get_subscription_keyboard()
        await callback.message.edit_text(
            f"⚠️ برای استفاده از ربات، ابتدا باید در کانال {CHANNEL_TITLE} عضو شوید.",
            reply_markup=subscription_keyboard
        )

@dp.message(Command("status"))
async def show_status_cmd(message: types.Message):
    """ نمایش وضعیت فعلی کاربر """
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
    
    partner_status = "❌ هیچ پارتنری ندارید."
    if partner_id:
        try:
            partner_info = await bot.get_chat(partner_id)
            partner_identifier = partner_info.username if partner_info.username else partner_info.first_name
            partner_status = f"✅ متصل به پارتنر: [{partner_identifier}](tg://user?id={partner_id})"
        except:
            partner_status = f"✅ متصل به پارتنر: [کاربر {partner_id}](tg://user?id={partner_id})"
    
    # ایجاد دکمه شیشه‌ای برای ارسال دعوتنامه
    inline_buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✉️ ارسال دعوتنامه به پارتنر", callback_data="send_invitation")]
        ]
    )
    
    await message.answer(
        f"📊 **وضعیت شما:**\n\n"
        f"🆔 آیدی شما: `{user_id}`\n"
        f"🔑 کد اختصاصی: `{unique_code}`\n"
        f"🎯 تعداد چالش‌های پاسخ داده شده: {answered_challenges}\n\n"
        f"{partner_status}",
        parse_mode="Markdown"
    )
    
    # ارسال پیام دوم با دکمه شیشه‌ای
    await message.answer("برای ارسال دعوتنامه به پارتنر، از دکمه زیر استفاده کنید:", reply_markup=inline_buttons)

@dp.message(Command("reply"))
async def reply_to_user_cmd(message: types.Message):
    """ پاسخ به کاربر از طرف پشتیبانی """
    user_id = message.from_user.id
    
    # فقط ادمین می‌تواند از این دستور استفاده کند
    if user_id != ADMIN_ID:
        await message.answer("⛔️ شما مجاز به استفاده از این دستور نیستید.")
        return
    
    # بررسی فرمت صحیح دستور
    command_parts = message.text.split(maxsplit=2)
    if len(command_parts) < 3:
        await message.answer("⚠️ فرمت صحیح: /reply ID متن پیام")
        return
    
    try:
        target_user_id = int(command_parts[1])
        reply_text = command_parts[2]
        
        # بررسی وجود کاربر در دیتابیس
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (target_user_id,))
        if not cursor.fetchone():
            await message.answer(f"❌ کاربری با شناسه {target_user_id} یافت نشد.")
            return
        
        # ارسال پیام به کاربر
        await bot.send_message(
            target_user_id,
            f"👨‍💻 پاسخ از پشتیبانی:\n\n{reply_text}\n\n"
            f"برای ارسال پیام جدید به پشتیبانی از دستور /support استفاده کنید."
        )
        
        await message.answer(f"✅ پیام با موفقیت به کاربر {target_user_id} ارسال شد.")
        
    except ValueError:
        await message.answer("❌ شناسه کاربر باید یک عدد باشد.")
    except Exception as e:
        await message.answer(f"❌ خطا در ارسال پیام: {str(e)}")

@dp.message(Command("support"))
async def support_cmd(message: types.Message):
    """ ارتباط با پشتیبانی """
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
    
    # ساخت کیبورد برای انتخاب نوع درخواست پشتیبانی
    support_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔧 مشکل فنی", callback_data="support_technical")],
        [InlineKeyboardButton(text="❓ سوال و راهنمایی", callback_data="support_question")],
        [InlineKeyboardButton(text="💡 پیشنهاد", callback_data="support_suggestion")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="cancel_support")]
    ])
    
    await message.answer(
        "👨‍💻 به بخش پشتیبانی خوش آمدید!\n"
        "لطفاً نوع درخواست خود را انتخاب کنید:",
        reply_markup=support_keyboard
    )

@dp.callback_query(lambda c: c.data.startswith("support_"))
async def support_type_callback(callback: types.CallbackQuery):
    """ پردازش انتخاب نوع پشتیبانی """
    user_id = callback.from_user.id
    
    # دریافت نوع درخواست پشتیبانی
    support_type = callback.data.split("_")[1]
    
    # ذخیره وضعیت کاربر برای دریافت پیام پشتیبانی
    cursor.execute("UPDATE users SET waiting_for_support = ? WHERE user_id = ?", (support_type, user_id))
    conn.commit()
    
    support_types = {
        "technical": "🔧 مشکل فنی",
        "question": "❓ سوال و راهنمایی",
        "suggestion": "💡 پیشنهاد"
    }
    
    await callback.message.edit_text(
        f"✅ شما در حال ارسال {support_types[support_type]} هستید.\n\n"
        "📝 لطفاً پیام خود را برای تیم پشتیبانی بنویسید و ارسال کنید.\n"
        "(می‌توانید متن، عکس، ویدیو یا صدا ارسال کنید)"
    )
    
    # ایجاد دکمه لغو درخواست
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 لغو درخواست", callback_data="cancel_support")]
    ])
    
    await callback.message.answer("برای لغو درخواست، روی دکمه زیر کلیک کنید:", reply_markup=cancel_keyboard)

@dp.callback_query(lambda c: c.data == "cancel_support")
async def cancel_support_callback(callback: types.CallbackQuery):
    """ لغو درخواست پشتیبانی """
    user_id = callback.from_user.id
    
    # پاک کردن وضعیت انتظار برای پشتیبانی
    cursor.execute("UPDATE users SET waiting_for_support = NULL WHERE user_id = ?", (user_id,))
    conn.commit()
    
    await callback.message.edit_text("❌ درخواست پشتیبانی لغو شد.")

@dp.message()
async def process_message(message: types.Message):
    """پردازش پیام‌های معمولی (غیر دستوری)"""
    user_id = message.from_user.id
    
    # بررسی آیا پیام یکی از دکمه‌های منو است
    if message.text == "⭐️ دریافت چالش جدید":
        await challenge_button(message)
        return
    elif message.text == "🔄 وضعیت من":
        await status_button(message)
        return
    elif message.text == "👥 پارتنر من":
        await partner_button(message)
        return
    elif message.text == "📨 پیام به پارتنر":
        await message_button(message)
        return
    elif message.text == "📞 پشتیبانی":
        await support_button(message)
        return
    elif message.text == "⚙️ پنل مدیریت":
        await admin_panel_btn(message)
        return
    # بررسی آیا پیام دستور broadcast است
    elif message.text and message.text.startswith("/broadcast "):
        await broadcast_cmd(message)
        return
    
    # به‌روزرسانی اطلاعات کاربر برای آمارگیری بهتر
    # این کار به ما کمک می‌کند اطلاعات کاربران را کامل‌تر داشته باشیم
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    cursor.execute("""
        UPDATE users 
        SET username = ?, first_name = ?, last_name = ?
        WHERE user_id = ?
    """, (username, first_name, last_name, user_id))
    conn.commit()
    
    # بررسی عضویت کاربر در کانال
    is_subscribed = await check_subscription(user_id)
    if not is_subscribed:
        subscription_keyboard = get_subscription_keyboard()
        await message.answer(
            f"⚠️ برای استفاده از ربات، ابتدا باید در کانال {CHANNEL_TITLE} عضو شوید.",
            reply_markup=subscription_keyboard
        )
        return
    
    # بررسی حساب کاربری
    cursor.execute("SELECT unique_code, partner_id, waiting_for_code, waiting_for_support FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()
    
    if not user_data:
        await message.answer("⚠️ اطلاعات شما در سیستم یافت نشد. لطفاً دوباره /start را ارسال کنید.")
        return
    
    unique_code, partner_id, waiting_for_code, waiting_for_support = user_data
    
    # بررسی آیا کاربر در حال ارسال پیام پشتیبانی است
    if waiting_for_support:
        # دریافت اطلاعات کاربر
        try:
            user_info = await bot.get_chat(user_id)
            user_name = user_info.username if user_info.username else user_info.first_name
        except Exception as e:
            print(f"خطا در دریافت اطلاعات کاربر برای پشتیبانی: {e}")
            user_name = str(user_id)
            
        # تعیین نوع پیام پشتیبانی
        support_types = {
            "technical": "🔧 مشکل فنی",
            "question": "❓ سوال و راهنمایی",
            "suggestion": "💡 پیشنهاد"
        }
        
        support_type_text = support_types.get(waiting_for_support, "درخواست پشتیبانی")
        
        try:
            # ارسال پیام کاربر به پشتیبانی
            support_message = f"📨 {support_type_text} از کاربر:\n\n"
            support_message += f"👤 کاربر: {user_name} (ID: {user_id})\n\n"
            
            # تشخیص نوع پیام (متن، عکس، ویدیو و...)
            media_id = None
            media_type = None
            
            if message.text:
                support_message += f"📝 پیام: {message.text}"
                
                await bot.send_message(SUPPORT_CHAT_ID, support_message)
                print(f"پیام پشتیبانی متنی به {SUPPORT_CHAT_ID} ارسال شد")
            else:
                support_message += "📎 پیام حاوی مدیا است:"
                await bot.send_message(SUPPORT_CHAT_ID, support_message)
                print(f"پیام پشتیبانی مدیا به {SUPPORT_CHAT_ID} ارسال شد")
                
                if message.photo:
                    media_id = message.photo[-1].file_id
                    media_type = "photo"
                    caption = message.caption or ""
                    await bot.send_photo(SUPPORT_CHAT_ID, media_id, caption=f"🖼️ تصویر ارسالی از کاربر\n{caption}")
                
                elif message.video:
                    media_id = message.video.file_id
                    media_type = "video"
                    caption = message.caption or ""
                    await bot.send_video(SUPPORT_CHAT_ID, media_id, caption=f"🎬 ویدیوی ارسالی از کاربر\n{caption}")
                
                elif message.voice:
                    media_id = message.voice.file_id
                    media_type = "voice"
                    await bot.send_voice(SUPPORT_CHAT_ID, media_id, caption=f"🎤 صدای ارسالی از کاربر")
                
                elif message.video_note:
                    media_id = message.video_note.file_id
                    media_type = "video_note"
                    await bot.send_video_note(SUPPORT_CHAT_ID, media_id)
                    await bot.send_message(SUPPORT_CHAT_ID, f"🎥 ویدیو مسیج ارسالی از کاربر {user_name}")
                
                elif message.sticker:
                    media_id = message.sticker.file_id
                    media_type = "sticker"
                    await bot.send_sticker(SUPPORT_CHAT_ID, media_id)
                    await bot.send_message(SUPPORT_CHAT_ID, f"🏷️ استیکر ارسالی از کاربر {user_name}")
            
            # تایید دریافت پیام پشتیبانی به کاربر
            await message.answer("✅ پیام شما با موفقیت به تیم پشتیبانی ارسال شد.\nدر اسرع وقت به شما پاسخ خواهیم داد.")
            
        except Exception as e:
            print(f"خطا در ارسال پیام پشتیبانی: {e}")
            await message.answer("❌ خطایی در ارسال پیام به پشتیبانی رخ داد. لطفاً دوباره تلاش کنید.")
        
        # پاک کردن وضعیت انتظار برای پشتیبانی
        cursor.execute("UPDATE users SET waiting_for_support = NULL WHERE user_id = ?", (user_id,))
        conn.commit()
        
        return
    
    # بررسی کد پارتنر
    if waiting_for_code:
        try:
            input_code = message.text.strip()
            
            # بررسی صحت کد
            cursor.execute("SELECT user_id FROM users WHERE unique_code=?", (input_code,))
            result = cursor.fetchone()
            
            if not result:
                await message.answer("❌ کد نامعتبر است. لطفاً یک کد معتبر وارد کنید.")
                return
                
            partner_id = result[0]
            
            # بررسی اینکه آیا خود کاربر است
            if user_id == partner_id:
                await message.answer("❌ شما نمی‌توانید به خودتان متصل شوید!")
                # بروزرسانی وضعیت انتظار برای کد
                cursor.execute("UPDATE users SET waiting_for_code=0 WHERE user_id=?", (user_id,))
                conn.commit()
                return
            
            # بررسی مجدد اینکه آیا کاربر هنوز به کسی متصل است
            cursor.execute("SELECT partner_id FROM users WHERE user_id=?", (user_id,))
            user_data = cursor.fetchone()
            
            if user_data and user_data[0]:
                # ایجاد دکمه برای قطع ارتباط
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="❌ قطع ارتباط با پارتنر فعلی", callback_data="disconnect_partner")]
                    ]
                )
                await message.answer("⚠️ شما هنوز به پارتنر دیگری متصل هستید. لطفاً ابتدا ارتباط فعلی خود را قطع کنید.", reply_markup=keyboard)
                # بروزرسانی وضعیت انتظار برای کد
                cursor.execute("UPDATE users SET waiting_for_code=0 WHERE user_id=?", (user_id,))
                conn.commit()
                return
            
            # بررسی اینکه آیا پارتنر قبلاً به کسی متصل است
            cursor.execute("SELECT partner_id FROM users WHERE user_id=?", (partner_id,))
            partner_data = cursor.fetchone()
            
            if partner_data and partner_data[0]:
                await message.answer("❌ کاربر مورد نظر قبلاً به پارتنر دیگری متصل شده است. لطفاً از او بخواهید ابتدا ارتباط فعلی خود را قطع کند.")
                # بروزرسانی وضعیت انتظار برای کد
                cursor.execute("UPDATE users SET waiting_for_code=0 WHERE user_id=?", (user_id,))
                conn.commit()
                return
                
            # بروزرسانی وضعیت انتظار برای کد قبل از اتصال
            cursor.execute("UPDATE users SET waiting_for_code=0 WHERE user_id=?", (user_id,))
            conn.commit()
            
            # اتصال به پارتنر
            await process_partner_connection(message, partner_id)
            
        except Exception as e:
            # بروزرسانی وضعیت انتظار برای کد در صورت خطا
            cursor.execute("UPDATE users SET waiting_for_code=0 WHERE user_id=?", (user_id,))
            conn.commit()
            
            await message.answer("❌ خطا در پردازش کد. لطفاً مجدداً تلاش کنید.")
        
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
        elif message.text.startswith("/support") or "پشتیبانی" in message.text:
            await support_cmd(message)
            return
        elif message.text.startswith("/challenge") or "دریافت چالش جدید" in message.text:
            await new_challenge_cmd(message)
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
        else:
            answer_text = "بدون متن"
            
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
        try:
            cursor.execute("UPDATE questions SET answer = ? WHERE id = ?", (answer_text, question_id))
            conn.commit()
            
            await message.answer("✅ پاسخ شما به چالش ذخیره شد.")
            
            # بررسی آیا پارتنر هم پاسخ داده است
            cursor.execute("SELECT answer FROM questions WHERE user_id = ? AND partner_id = ? AND question = ?", 
                           (partner_id, user_id, question_text))
            partner_answer = cursor.fetchone()
            
            # تهیه اطلاعات برای ادمین
            try:
                user_info = await bot.get_chat(user_id)
                user_identifier = user_info.username if user_info.username else user_info.first_name
            except:
                user_identifier = str(user_id)
            
            admin_notification = f"🔔 کاربر {user_identifier} به چالش پاسخ داد:\n"
            admin_notification += f"سوال: {question_text}\n"
            admin_notification += f"پاسخ: {answer_text or 'بدون متن'}"
            
            # ارسال اطلاعات به ادمین
            await bot.send_message(SUPPORT_CHAT_ID, admin_notification)
            
            # ارسال مدیا به ادمین
            if media_type and media_id:
                try:
                    if media_type == "photo":
                        await bot.send_photo(SUPPORT_CHAT_ID, media_id, caption=f"📷 تصویر پاسخ کاربر {user_identifier}")
                    elif media_type == "video":
                        await bot.send_video(SUPPORT_CHAT_ID, media_id, caption=f"🎬 ویدیوی پاسخ کاربر {user_identifier}")
                    elif media_type == "voice":
                        await bot.send_voice(SUPPORT_CHAT_ID, media_id, caption=f"🎤 صدای پاسخ کاربر {user_identifier}")
                    elif media_type == "video_note":
                        await bot.send_video_note(SUPPORT_CHAT_ID, media_id)
                except Exception as e:
                    print(f"خطا در ارسال مدیا به ادمین: {e}")
            
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
                
                # ارسال مدیا (در صورت وجود) به پارتنر
                if media_type and media_id:
                    try:
                        if media_type == "photo":
                            await bot.send_photo(partner_id, media_id, caption="📷 تصویر پاسخ پارتنر شما")
                        elif media_type == "video":
                            await bot.send_video(partner_id, media_id, caption="🎬 ویدیوی پاسخ پارتنر شما")
                        elif media_type == "voice":
                            await bot.send_voice(partner_id, media_id, caption="🎤 صدای پاسخ پارتنر شما")
                        elif media_type == "video_note":
                            await bot.send_video_note(partner_id, media_id)
                    except Exception as e:
                        print(f"خطا در ارسال مدیا به پارتنر: {e}")
                
                # بررسی همه سوالات بی‌پاسخ
                cursor.execute("SELECT COUNT(*) FROM questions WHERE (user_id = ? OR user_id = ?) AND answer IS NULL", 
                              (user_id, partner_id))
                unanswered_count = cursor.fetchone()[0]
                
                # ارسال سوال جدید اگر همه سوالات پاسخ داده شده‌اند
                if unanswered_count == 0:
                    await send_question(user_id, partner_id)
            else:
                # اطلاع به پارتنر که کاربر پاسخ داده است
                await bot.send_message(partner_id, f"💡 پارتنر شما به چالش اخیر پاسخ داده است. منتظر پاسخ شما هستیم!")
            
            # توقف پردازش بیشتر پیام، چون این یک پاسخ به چالش بود
            return
        
        except Exception as e:
            print(f"خطا در ذخیره پاسخ: {e}")
            await message.answer("❌ خطایی در ذخیره پاسخ رخ داد. لطفاً دوباره تلاش کنید.")
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
    
    await bot.send_message(SUPPORT_CHAT_ID, admin_message)
    
    # ارسال مدیا به ادمین
    if media_type and media_id:
        admin_media_caption = f"🔄 مدیا از کاربر {user_id} به کاربر {partner_id}"
        if message_text:
            admin_media_caption += f"\nپیام: {message_text}"
            
        if media_type == "photo":
            await bot.send_photo(SUPPORT_CHAT_ID, media_id, caption=admin_media_caption)
        elif media_type == "video":
            await bot.send_video(SUPPORT_CHAT_ID, media_id, caption=admin_media_caption)
        elif media_type == "voice":
            await bot.send_voice(SUPPORT_CHAT_ID, media_id, caption=admin_media_caption)
        elif media_type == "video_note":
            await bot.send_message(SUPPORT_CHAT_ID, f"🔄 کاربر {user_id} یک ویدیو مسیج برای کاربر {partner_id} ارسال کرد")
            await bot.send_video_note(SUPPORT_CHAT_ID, media_id)
        elif media_type == "sticker":
            await bot.send_message(SUPPORT_CHAT_ID, f"🔄 کاربر {user_id} یک استیکر برای کاربر {partner_id} ارسال کرد")
            await bot.send_sticker(SUPPORT_CHAT_ID, media_id)

async def process_partner_connection(message: types.Message, partner_id: int):
    """ پردازش اتصال به پارتنر """
    user_id = message.from_user.id
    
    try:
        # دریافت اطلاعات کاربران
        cursor.execute("SELECT unique_code FROM users WHERE user_id=?", (user_id,))
        user_code = cursor.fetchone()[0]
        
        # بررسی چالش‌های بی‌پاسخ قبلی بین این دو کاربر
        cursor.execute("SELECT id, question FROM questions WHERE user_id = ? AND partner_id = ? AND answer IS NULL", (user_id, partner_id))
        user_unanswered = cursor.fetchone()
        
        cursor.execute("SELECT id, question FROM questions WHERE user_id = ? AND partner_id = ? AND answer IS NULL", (partner_id, user_id))
        partner_unanswered = cursor.fetchone()
        
        # حذف چالش‌های بی‌پاسخ قبلی با پارتنرهای دیگر (برای هر دو کاربر)
        # برای کاربر اصلی
        cursor.execute("DELETE FROM questions WHERE user_id = ? AND partner_id != ? AND answer IS NULL", (user_id, partner_id))
        # برای پارتنر جدید
        cursor.execute("DELETE FROM questions WHERE user_id = ? AND partner_id != ? AND answer IS NULL", (partner_id, user_id))
        
        # اتصال کاربران به یکدیگر
        cursor.execute("UPDATE users SET partner_id=? WHERE user_id=?", (partner_id, user_id))
        cursor.execute("UPDATE users SET partner_id=? WHERE user_id=?", (user_id, partner_id))
        conn.commit()
        
        # ارسال پیام تایید به هر دو کاربر
        try:
            # اطلاعات برای نمایش
            user_info = await bot.get_chat(user_id)
            partner_info = await bot.get_chat(partner_id)
            
            user_identifier = user_info.username if user_info.username else user_info.first_name
            partner_identifier = partner_info.username if partner_info.username else partner_info.first_name
            
            # ارسال پیام به کاربران
            await message.answer(f"✅ شما با موفقیت به {partner_identifier} متصل شدید!\n\nاکنون می‌توانید پیام ارسال کنید و به صورت روزانه چالش‌های مشترک دریافت کنید.")
            await bot.send_message(partner_id, f"✅ {user_identifier} با شما متصل شد!\n\nاکنون می‌توانید پیام ارسال کنید و به صورت روزانه چالش‌های مشترک دریافت کنید.")
            
            # اطلاع به ادمین
            await bot.send_message(
                SUPPORT_CHAT_ID, 
                f"🔗 اتصال جدید:\n{user_identifier} به {partner_identifier} متصل شد."
            )
            
            # مکث کوتاه
            await asyncio.sleep(2)
            
            # بررسی آیا این دو کاربر قبلاً چالش بی‌پاسخی داشته‌اند
            has_unanswered_challenges = False
            
            if user_unanswered:
                has_unanswered_challenges = True
                await bot.send_message(user_id, f"⚠️ یادآوری: شما هنوز به این چالش قبلی پاسخ نداده‌اید:\n\n{user_unanswered[1]}\n\n✏️ لطفاً پاسخ خود را ارسال کنید.")
            
            if partner_unanswered:
                has_unanswered_challenges = True
                await bot.send_message(partner_id, f"⚠️ یادآوری: شما هنوز به این چالش قبلی پاسخ نداده‌اید:\n\n{partner_unanswered[1]}\n\n✏️ لطفاً پاسخ خود را ارسال کنید.")
            
            # همیشه یک چالش جدید ارسال می‌کنیم مگر اینکه چالش بی‌پاسخی از قبل وجود داشته باشد
            if not has_unanswered_challenges:
                # ارسال اولین سوال چالشی - با پارامتر force=True برای نادیده گرفتن محدودیت زمانی
                await send_question(user_id, partner_id, force=True)
            
            return True
            
        except Exception as e:
            print(f"Error sending connection messages: {e}")
            # با وجود خطا در ارسال پیام، اتصال انجام شده است
            # بنابراین پیام خطا نشان نمی‌دهیم
            return True
            
    except Exception as e:
        print(f"Error in process_partner_connection: {e}")
        # فقط اگر خطای اصلی در اتصال رخ داده باشد، پیام خطا نمایش می‌دهیم
        await message.answer("❌ خطایی در اتصال به پارتنر رخ داد. لطفاً دوباره تلاش کنید.")
        return False

@dp.callback_query(lambda c: c.data == "send_invitation")
async def send_invitation_callback(callback_query: types.CallbackQuery):
    """ ارسال دعوتنامه به پارتنر """
    user_id = callback_query.from_user.id
    
    # بررسی اطلاعات کاربر
    cursor.execute("SELECT unique_code FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    
    if not result:
        await callback_query.answer("⚠️ اطلاعات شما یافت نشد. لطفاً دوباره /start را ارسال کنید.", show_alert=True)
        return
    
    unique_code = result[0]
    user_name = callback_query.from_user.first_name
    
    # متن دعوتنامه
    invitation_text = f"""🌹 سلام عزیزم!

من در ربات چالش عاشقانه @challeshhamdelibot ثبت‌نام کردم و می‌خوام با تو به چالش‌های هیجان‌انگیز پاسخ بدم.

با این ربات می‌تونیم به سوالات جالب در مورد رابطه‌مون پاسخ بدیم و بیشتر همدیگه رو بشناسیم.

♥️ برای اتصال به من، کافیه این مراحل رو انجام بدی:
1️⃣ وارد ربات شو: @challeshhamdelibot
2️⃣ دستور /start رو بزن
3️⃣ عضو کانال ربات شو
4️⃣ روی دکمه "🔗 اتصال به پارتنر" بزن
5️⃣ این کد رو وارد کن: {unique_code}

منتظرتم... 😊

با عشق، {user_name}"""

    # ارسال پیام دعوتنامه به کاربر
    await callback_query.message.answer(invitation_text)
    await callback_query.answer("✅ متن دعوتنامه ایجاد شد. آن را برای پارتنر خود ارسال کنید.", show_alert=True)

# ایجاد دکمه برای درخواست چالش جدید
def get_main_menu_keyboard():
    """ ایجاد کیبورد منوی اصلی """
    menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⭐️ دریافت چالش جدید")],
            [KeyboardButton(text="🔄 وضعیت من"), KeyboardButton(text="👥 پارتنر من")],
            [KeyboardButton(text="📨 پیام به پارتنر"), KeyboardButton(text="📞 پشتیبانی")]
        ],
        resize_keyboard=True
    )
    
    return menu

def get_admin_menu_keyboard():
    """ ایجاد کیبورد منوی اصلی برای ادمین """
    menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⭐️ دریافت چالش جدید")],
            [KeyboardButton(text="🔄 وضعیت من"), KeyboardButton(text="👥 پارتنر من")],
            [KeyboardButton(text="📨 پیام به پارتنر"), KeyboardButton(text="📞 پشتیبانی")],
            [KeyboardButton(text="⚙️ پنل مدیریت")]
        ],
        resize_keyboard=True
    )
    
    return menu

# افزودن هندلر جدید برای درخواست چالش جدید
@dp.message(Command("challenge"))
async def new_challenge_cmd(message: types.Message):
    """ درخواست دریافت چالش جدید """
    user_id = message.from_user.id
    
    # بررسی عضویت کاربر در کانال
    if not await check_user_subscription(message):
        return
    
    # بررسی وجود پارتنر
    cursor.execute("SELECT partner_id FROM users WHERE user_id=?", (user_id,))
    partner = cursor.fetchone()
    
    if not partner or not partner[0]:
        await message.answer("⚠️ شما هنوز به پارتنری متصل نشده‌اید. لطفاً ابتدا با استفاده از دستور /connect یا دکمه مربوطه به یک پارتنر متصل شوید.")
        return
    
    partner_id = partner[0]
    
    # ارسال چالش جدید با استفاده از پارامتر force=True
    result = await send_question(user_id, partner_id, force=True)
    
    if result:
        await message.answer("✅ چالش جدید برای شما و پارتنر شما ارسال شد!")
    else:
        await message.answer("⚠️ امکان ارسال چالش جدید در حال حاضر وجود ندارد. لطفاً ابتدا به چالش قبلی پاسخ دهید.")

async def main():
    # به‌روزرسانی timestamp برای تمام سوالات بی‌پاسخ فعلی
    current_time = int(time.time())
    cursor.execute("UPDATE questions SET timestamp = ? WHERE answer IS NULL AND (timestamp IS NULL OR timestamp = 0)", (current_time,))
    conn.commit()
    print("✅ timestamp همه سوالات بی‌پاسخ به‌روزرسانی شد.")
    
    # شروع تسک ارسال سوالات زمان‌بندی شده
    asyncio.create_task(scheduled_questions())
    
    # شروع تسک ارسال یادآوری‌ها
    asyncio.create_task(send_reminders())
    
    # شروع پالسینگ ربات
    await dp.start_polling(bot)

@dp.message(Command("broadcast"))
async def broadcast_cmd(message: types.Message):
    """ارسال پیام گروهی به تمامی کاربران ربات (فقط برای ادمین)"""
    user_id = message.from_user.id
    
    # بررسی دسترسی ادمین
    if user_id != ADMIN_ID:
        await message.answer("⛔️ شما دسترسی به این بخش را ندارید.")
        return
    
    # بررسی متن پیام
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer("⚠️ لطفا پیام خود را بعد از دستور /broadcast وارد کنید.")
        return
    
    broadcast_message = command_parts[1]
    
    # دریافت لیست تمام کاربران
    cursor.execute("SELECT user_id FROM users")
    all_users = cursor.fetchall()
    
    success_count = 0
    fail_count = 0
    
    await message.answer("🔄 در حال ارسال پیام گروهی...")
    
    # ارسال پیام به تمام کاربران
    for user in all_users:
        try:
            await bot.send_message(user[0], f"📢 پیام از طرف مدیریت ربات:\n\n{broadcast_message}")
            success_count += 1
            # کمی تاخیر برای جلوگیری از محدودیت‌های تلگرام
            await asyncio.sleep(0.05)
        except Exception:
            fail_count += 1
    
    # گزارش نتیجه به ادمین
    await message.answer(
        f"✅ گزارش ارسال پیام گروهی:\n"
        f"📨 ارسال موفق: {success_count}\n"
        f"❌ ارسال ناموفق: {fail_count}\n"
        f"📊 مجموع: {len(all_users)}"
    )

@dp.message(Command("stats"))
async def stats_cmd(message: types.Message):
    """نمایش آمار و اطلاعات پیشرفته ربات (فقط برای ادمین)"""
    user_id = message.from_user.id
    
    # بررسی دسترسی ادمین
    if user_id != ADMIN_ID:
        await message.answer("⛔️ شما دسترسی به این بخش را ندارید.")
        return
    
    # جمع‌آوری آمار کاربران
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE partner_id IS NOT NULL")
    connected_users = cursor.fetchone()[0]
    
    # تعداد پیام‌های تبادل شده
    cursor.execute("SELECT COUNT(*) FROM messages")
    total_messages = cursor.fetchone()[0]
    
    # تعداد سوالات و پاسخ‌ها
    cursor.execute("SELECT COUNT(*) FROM questions")
    total_questions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM questions WHERE answer IS NOT NULL")
    answered_questions = cursor.fetchone()[0]
    
    # کاربران فعال در ۲۴ ساعت گذشته (براساس پیام یا سوال)
    yesterday_timestamp = int(time.time()) - (24 * 3600)
    cursor.execute("""
        SELECT COUNT(DISTINCT user_id) FROM (
            SELECT sender_id as user_id FROM messages WHERE id IN (
                SELECT MAX(id) FROM messages GROUP BY sender_id
            ) AND id IN (
                SELECT id FROM messages WHERE id > (
                    SELECT COALESCE(MAX(id), 0) FROM messages WHERE sender_id = ? 
                    AND id IN (SELECT MAX(id) FROM messages GROUP BY sender_id)
                ) - 100
            )
            UNION
            SELECT user_id FROM questions WHERE timestamp > ?
        )
    """, (ADMIN_ID, yesterday_timestamp))
    active_users_24h = cursor.fetchone()[0]
    
    # نمایش آمار به ادمین
    stats_message = (
        "📊 **آمار و اطلاعات ربات**\n\n"
        f"👥 **کاربران**:\n"
        f"📌 کل کاربران: {total_users}\n"
        f"🔗 کاربران متصل شده: {connected_users}\n"
        f"🚀 کاربران فعال (۲۴ ساعت اخیر): {active_users_24h}\n\n"
        f"💬 **پیام‌ها و سوالات**:\n"
        f"📨 کل پیام‌های ارسالی: {total_messages}\n"
        f"❓ کل سوالات: {total_questions}\n"
        f"✅ سوالات پاسخ داده شده: {answered_questions}\n"
        f"⏳ سوالات بی‌پاسخ: {total_questions - answered_questions}\n\n"
        f"📈 **نرخ‌ها**:\n"
        f"💑 نرخ اتصال: {(connected_users / total_users * 100) if total_users > 0 else 0:.1f}%\n"
        f"📝 نرخ پاسخگویی: {(answered_questions / total_questions * 100) if total_questions > 0 else 0:.1f}%"
    )
    
    # ایجاد کیبورد برای عملیات‌های مدیریتی
    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 آمار جزئی‌تر", callback_data="detailed_stats"),
                InlineKeyboardButton(text="📱 کاربران فعال", callback_data="active_users")
            ],
            [
                InlineKeyboardButton(text="⚠️ پاکسازی غیرفعال‌ها", callback_data="purge_inactive"),
                InlineKeyboardButton(text="📨 پیام گروهی", callback_data="new_broadcast")
            ]
        ]
    )
    
    await message.answer(stats_message, reply_markup=admin_keyboard, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "detailed_stats")
async def detailed_stats_callback(callback: types.CallbackQuery):
    """نمایش آمار جزئی‌تر ربات"""
    user_id = callback.from_user.id
    
    # بررسی دسترسی ادمین
    if user_id != ADMIN_ID:
        await callback.answer("⛔️ شما دسترسی به این بخش را ندارید.", show_alert=True)
        return
    
    # آمار کاربران جدید طی هفته اخیر
    week_ago = int(time.time()) - (7 * 24 * 3600)
    cursor.execute("""
        SELECT COUNT(*) FROM users 
        WHERE user_id IN (
            SELECT MIN(user_id) FROM users 
            GROUP BY user_id
            HAVING MIN(rowid) IN (
                SELECT rowid FROM users 
                WHERE rowid > (SELECT MAX(rowid) FROM users) - 100
            )
        )
    """)
    new_users_week = cursor.fetchone()[0]
    
    # آمار فعالیت کاربران
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN partner_id IS NOT NULL THEN 1 END) as connected,
            COUNT(CASE WHEN partner_id IS NULL THEN 1 END) as single
        FROM users
    """)
    connected, single = cursor.fetchone()
    
    # میانگین تعداد پیام‌های ارسالی هر کاربر
    cursor.execute("""
        SELECT AVG(msg_count) FROM (
            SELECT sender_id, COUNT(*) as msg_count FROM messages
            GROUP BY sender_id
        )
    """)
    avg_messages = cursor.fetchone()[0]
    
    # تعداد چالش‌های فعال
    cursor.execute("SELECT COUNT(*) FROM questions WHERE answer IS NULL")
    active_challenges = cursor.fetchone()[0]
    
    detailed_stats = (
        "📈 **آمار تفصیلی ربات**\n\n"
        f"👤 **کاربران**:\n"
        f"🆕 کاربران جدید (هفته اخیر): {new_users_week}\n"
        f"🔄 نسبت کاربران متصل به مجرد: {connected}:{single}\n\n"
        f"💬 **فعالیت**:\n"
        f"📊 میانگین پیام هر کاربر: {avg_messages:.1f}\n"
        f"🎯 چالش‌های فعال: {active_challenges}\n\n"
        f"⏱ آمار به‌روزرسانی شد: {time.strftime('%H:%M:%S')}"
    )
    
    # دکمه بازگشت به منوی اصلی آمار
    back_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 بازگشت به منوی آمار", callback_data="back_to_stats")]
        ]
    )
    
    await callback.message.edit_text(detailed_stats, reply_markup=back_button, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "active_users")
async def active_users_callback(callback: types.CallbackQuery):
    """نمایش لیست کاربران فعال اخیر"""
    user_id = callback.from_user.id
    
    # بررسی دسترسی ادمین
    if user_id != ADMIN_ID:
        await callback.answer("⛔️ شما دسترسی به این بخش را ندارید.", show_alert=True)
        return
    
    # دریافت لیست کاربران فعال در هفته اخیر
    week_ago = int(time.time()) - (7 * 24 * 3600)
    cursor.execute("""
        SELECT DISTINCT u.user_id, u.username, u.first_name, u.last_name 
        FROM users u
        JOIN messages m ON u.user_id = m.sender_id
        WHERE m.id IN (
            SELECT MAX(id) FROM messages
            WHERE sender_id = u.user_id
            GROUP BY sender_id
        )
        ORDER BY m.id DESC
        LIMIT 20
    """)
    
    active_users = cursor.fetchall()
    
    if not active_users:
        await callback.message.edit_text(
            "⚠️ هیچ کاربر فعالی یافت نشد.", 
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_stats")]]
            )
        )
        await callback.answer()
        return
    
    active_users_text = "👥 **۲۰ کاربر فعال اخیر**:\n\n"
    
    for i, (uid, username, fname, lname) in enumerate(active_users, 1):
        display_name = fname or username or "بدون نام"
        if lname:
            display_name += f" {lname}"
        active_users_text += f"{i}. [{display_name}](tg://user?id={uid})"
        if username:
            active_users_text += f" - @{username}"
        active_users_text += "\n"
    
    # دکمه بازگشت
    back_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 بازگشت به منوی آمار", callback_data="back_to_stats")]
        ]
    )
    
    await callback.message.edit_text(active_users_text, reply_markup=back_button, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_to_stats")
async def back_to_stats_callback(callback: types.CallbackQuery):
    """بازگشت به منوی اصلی آمار"""
    # فراخوانی مجدد تابع آمار
    message = callback.message
    # ایجاد یک پیام مجازی برای فراخوانی تابع stats_cmd
    mock_message = types.Message(
        message_id=message.message_id,
        date=message.date,
        chat=message.chat,
        from_user=callback.from_user,
        text="/stats",
        bot=bot,
        reply_to_message=None,
        sender_chat=None,
        forward_from=None,
        forward_from_chat=None,
        forward_from_message_id=None,
        forward_signature=None,
        forward_date=None,
        reply_to_message_id=None,
        media_group_id=None,
        author_signature=None,
        entities=None,
        caption=None,
        caption_entities=None,
        has_protected_content=None,
        edit_date=None,
        is_topic_message=None,
        message_thread_id=None,
        forum_topic_created=None,
        forum_topic_closed=None,
        forum_topic_reopened=None,
        forum_topic_edited=None,
        general_forum_topic_hidden=None,
        general_forum_topic_unhidden=None,
        via_bot=None,
        restrict_content=None,
        web_page_preview=None
    )
    await stats_cmd(mock_message)
    await callback.message.delete()
    await callback.answer()

@dp.callback_query(lambda c: c.data == "new_broadcast")
async def new_broadcast_callback(callback: types.CallbackQuery):
    """شروع مراحل ارسال پیام گروهی جدید"""
    user_id = callback.from_user.id
    
    # بررسی دسترسی ادمین
    if user_id != ADMIN_ID:
        await callback.answer("⛔️ شما دسترسی به این بخش را ندارید.", show_alert=True)
        return
    
    await callback.message.answer(
        "📣 **ارسال پیام گروهی جدید**\n\n"
        "لطفا متن پیام گروهی خود را با فرمت زیر ارسال کنید:\n\n"
        "`/broadcast متن پیام شما در اینجا`\n\n"
        "⚠️ توجه: این پیام به تمامی کاربران ربات ارسال خواهد شد."
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "purge_inactive")
async def purge_inactive_callback(callback: types.CallbackQuery):
    """حذف کاربران غیرفعال (بیش از 3 ماه)"""
    user_id = callback.from_user.id
    
    # بررسی دسترسی ادمین
    if user_id != ADMIN_ID:
        await callback.answer("⛔️ شما دسترسی به این بخش را ندارید.", show_alert=True)
        return
    
    # کیبورد تایید
    confirm_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ بله، حذف شوند", callback_data="confirm_purge"),
                InlineKeyboardButton(text="❌ خیر، لغو عملیات", callback_data="cancel_purge")
            ]
        ]
    )
    
    three_months_ago = int(time.time()) - (90 * 24 * 3600)
    
    # شمارش کاربران غیرفعال
    cursor.execute("""
        SELECT COUNT(*) FROM users 
        WHERE user_id NOT IN (
            SELECT DISTINCT sender_id FROM messages 
            WHERE sender_id IN (SELECT user_id FROM users)
            AND id > (SELECT MAX(id) FROM messages) - 1000
        )
        AND user_id != ?
    """, (ADMIN_ID,))
    
    inactive_count = cursor.fetchone()[0]
    
    await callback.message.edit_text(
        f"⚠️ **حذف کاربران غیرفعال**\n\n"
        f"تعداد {inactive_count} کاربر غیرفعال شناسایی شدند.\n"
        f"آیا مطمئن هستید که می‌خواهید این کاربران را حذف کنید؟",
        reply_markup=confirm_keyboard
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "confirm_purge")
async def confirm_purge_callback(callback: types.CallbackQuery):
    """تایید و انجام عملیات حذف کاربران غیرفعال"""
    user_id = callback.from_user.id
    
    # بررسی دسترسی ادمین
    if user_id != ADMIN_ID:
        await callback.answer("⛔️ شما دسترسی به این بخش را ندارید.", show_alert=True)
        return
    
    three_months_ago = int(time.time()) - (90 * 24 * 3600)
    
    # شناسایی کاربران غیرفعال
    cursor.execute("""
        SELECT user_id FROM users 
        WHERE user_id NOT IN (
            SELECT DISTINCT sender_id FROM messages 
            WHERE sender_id IN (SELECT user_id FROM users)
            AND id > (SELECT MAX(id) FROM messages) - 1000
        )
        AND user_id != ?
    """, (ADMIN_ID,))
    
    inactive_users = [user[0] for user in cursor.fetchall()]
    
    if not inactive_users:
        await callback.message.edit_text("✅ هیچ کاربر غیرفعالی برای حذف یافت نشد.")
        await callback.answer()
        return
    
    # حذف کاربران غیرفعال
    for user_id in inactive_users:
        # ابتدا حذف پیام‌ها و سوالات مرتبط
        cursor.execute("DELETE FROM messages WHERE sender_id = ? OR receiver_id = ?", (user_id, user_id))
        cursor.execute("DELETE FROM questions WHERE user_id = ? OR partner_id = ?", (user_id, user_id))
        
        # سپس حذف خود کاربر
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    
    conn.commit()
    
    await callback.message.edit_text(
        f"✅ عملیات با موفقیت انجام شد.\n"
        f"تعداد {len(inactive_users)} کاربر غیرفعال حذف شدند."
    )
    await callback.answer("عملیات با موفقیت انجام شد", show_alert=True)

@dp.callback_query(lambda c: c.data == "cancel_purge")
async def cancel_purge_callback(callback: types.CallbackQuery):
    """لغو عملیات حذف کاربران غیرفعال"""
    user_id = callback.from_user.id
    
    # بررسی دسترسی ادمین
    if user_id != ADMIN_ID:
        await callback.answer("⛔️ شما دسترسی به این بخش را ندارید.", show_alert=True)
        return
    
    await callback.message.edit_text("❌ عملیات حذف کاربران غیرفعال لغو شد.")
    await callback.answer()

@dp.message(lambda message: message.text == "⚙️ پنل مدیریت")
async def admin_panel_btn(message: types.Message):
    """پاسخ به دکمه پنل مدیریت"""
    user_id = message.from_user.id
    
    # بررسی دسترسی ادمین
    if user_id != ADMIN_ID:
        await message.answer("⛔️ شما دسترسی به این بخش را ندارید.")
        return
    
    # ایجاد کیبورد اینلاین برای دستورات مدیریتی
    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 آمار ربات", callback_data="show_stats")],
            [InlineKeyboardButton(text="📢 ارسال پیام گروهی", callback_data="new_broadcast")],
            [InlineKeyboardButton(text="🗑 پاکسازی کاربران غیرفعال", callback_data="purge_inactive")],
        ]
    )
    
    await message.answer(
        "⚙️ **پنل مدیریت ربات**\n\n"
        "از طریق این بخش می‌توانید عملیات مدیریتی ربات را انجام دهید:",
        reply_markup=admin_keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data == "show_stats")
async def show_stats_callback(callback: types.CallbackQuery):
    """نمایش آمار ربات"""
    try:
        user_id = callback.from_user.id
        
        # بررسی دسترسی ادمین
        if user_id != ADMIN_ID:
            await callback.answer("⛔️ شما دسترسی به این بخش را ندارید.", show_alert=True)
            return
        
        # جمع‌آوری آمار کاربران به صورت مستقیم
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE partner_id IS NOT NULL")
        connected_users = cursor.fetchone()[0]
        
        # تعداد پیام‌های تبادل شده
        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]
        
        # تعداد سوالات و پاسخ‌ها
        cursor.execute("SELECT COUNT(*) FROM questions")
        total_questions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM questions WHERE answer IS NOT NULL")
        answered_questions = cursor.fetchone()[0]
        
        # کاربران فعال در ۲۴ ساعت گذشته (براساس پیام یا سوال)
        yesterday_timestamp = int(time.time()) - (24 * 3600)
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) FROM (
                SELECT sender_id as user_id FROM messages WHERE id IN (
                    SELECT MAX(id) FROM messages GROUP BY sender_id
                ) AND id IN (
                    SELECT id FROM messages WHERE id > (
                        SELECT COALESCE(MAX(id), 0) FROM messages WHERE sender_id = ? 
                        AND id IN (SELECT MAX(id) FROM messages GROUP BY sender_id)
                    ) - 100
                )
                UNION
                SELECT user_id FROM questions WHERE timestamp > ?
            )
        """, (ADMIN_ID, yesterday_timestamp))
        active_users_24h = cursor.fetchone()[0]
        
        # نمایش آمار به ادمین
        stats_message = (
            "📊 **آمار و اطلاعات ربات**\n\n"
            f"👥 **کاربران**:\n"
            f"📌 کل کاربران: {total_users}\n"
            f"🔗 کاربران متصل شده: {connected_users}\n"
            f"🚀 کاربران فعال (۲۴ ساعت اخیر): {active_users_24h}\n\n"
            f"💬 **پیام‌ها و سوالات**:\n"
            f"📨 کل پیام‌های ارسالی: {total_messages}\n"
            f"❓ کل سوالات: {total_questions}\n"
            f"✅ سوالات پاسخ داده شده: {answered_questions}\n"
            f"⏳ سوالات بی‌پاسخ: {total_questions - answered_questions}\n\n"
            f"📈 **نرخ‌ها**:\n"
            f"💑 نرخ اتصال: {(connected_users / total_users * 100) if total_users > 0 else 0:.1f}%\n"
            f"📝 نرخ پاسخگویی: {(answered_questions / total_questions * 100) if total_questions > 0 else 0:.1f}%"
        )
        
        # ایجاد کیبورد برای عملیات‌های مدیریتی
        admin_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="📊 آمار جزئی‌تر", callback_data="detailed_stats"),
                    InlineKeyboardButton(text="📱 کاربران فعال", callback_data="active_users")
                ],
                [
                    InlineKeyboardButton(text="⚠️ پاکسازی غیرفعال‌ها", callback_data="purge_inactive"),
                    InlineKeyboardButton(text="📨 پیام گروهی", callback_data="new_broadcast")
                ]
            ]
        )
        
        # سعی کن از ارسال پیام جدید به جای ویرایش استفاده کنی
        try:
            # ابتدا سعی می‌کنیم پیام را ویرایش کنیم
            await callback.message.edit_text(stats_message, reply_markup=admin_keyboard, parse_mode="Markdown")
        except Exception as edit_error:
            logging.error(f"خطا در ویرایش پیام آمار: {edit_error}")
            # اگر ویرایش با خطا مواجه شد، پیام را حذف کرده و یک پیام جدید ارسال می‌کنیم
            await callback.message.delete()
            await callback.message.answer(stats_message, reply_markup=admin_keyboard, parse_mode="Markdown")
        
        await callback.answer("آمار به‌روزرسانی شد")
    except Exception as e:
        logging.error(f"خطا در نمایش آمار: {e}")
        await callback.answer(f"خطایی رخ داد: {str(e)}", show_alert=True)
        try:
            # ارسال پیام ساده در صورت خطا
            await callback.message.answer(f"⚠️ خطایی در دریافت آمار رخ داد: {str(e)}")
        except Exception:
            # اگر ارسال پیام هم موفقیت‌آمیز نبود، نادیده بگیر
            pass

@dp.message(lambda message: message.text == "⭐️ دریافت چالش جدید")
async def challenge_button(message: types.Message):
    """دکمه دریافت چالش جدید"""
    # استفاده از تابع قبلی برای ارسال چالش
    await new_challenge_cmd(message)

@dp.message(lambda message: message.text == "🔄 وضعیت من")
async def status_button(message: types.Message):
    """دکمه نمایش وضعیت کاربر"""
    # استفاده از تابع قبلی برای نمایش وضعیت
    await show_status_cmd(message)

@dp.message(lambda message: message.text == "👥 پارتنر من")
async def partner_button(message: types.Message):
    """دکمه مدیریت پارتنر"""
    # استفاده از تابع قبلی برای مدیریت پارتنر
    await manage_partner_cmd(message)

@dp.message(lambda message: message.text == "📨 پیام به پارتنر")
async def message_button(message: types.Message):
    """دکمه ارسال پیام به پارتنر"""
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
    
    # بررسی وجود پارتنر
    cursor.execute("SELECT partner_id FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()
    
    if not user_data or not user_data[0]:
        # پارتنری وجود ندارد
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 اتصال به پارتنر", callback_data="start_connect")]
            ]
        )
        await message.answer("⚠️ شما هنوز به پارتنری متصل نیستید. ابتدا باید با کسی ارتباط برقرار کنید.", reply_markup=keyboard)
        return
    
    partner_id = user_data[0]
    
    # اطلاعات پارتنر
    try:
        partner_info = await bot.get_chat(partner_id)
        partner_name = partner_info.first_name or "پارتنر"
    except:
        partner_name = "پارتنر"
    
    # ارسال راهنمای ارسال پیام
    await message.answer(
        f"💬 *ارسال پیام به {partner_name}*\n\n"
        "پیام خود را بنویسید یا رسانه‌ای ارسال کنید. پیام شما مستقیماً برای پارتنر شما ارسال خواهد شد.\n\n"
        "💡 شما می‌توانید متن، عکس، ویدیو، صدا، استیکر و... ارسال کنید.",
        parse_mode="Markdown"
    )

@dp.message(lambda message: message.text == "📞 پشتیبانی")
async def support_button(message: types.Message):
    """دکمه پشتیبانی"""
    # استفاده از تابع قبلی برای پشتیبانی
    await support_cmd(message)

if __name__ == "__main__":
    asyncio.run(main()) 
