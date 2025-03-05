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

# لیست سوالات چالشی برای زوج‌ها
questions = [
    # سوالات عمومی رابطه
    "اگر یک آرزوی غیرممکن داشتی، چی بود؟",
    "بزرگترین ترس زندگیت چیه؟",
    "بهترین خاطره‌ای که با پارتنرت داری چیه؟",
    "اگر می‌تونستی یک چیز رو در زندگیت تغییر بدی، چی بود؟",
    "اولین باری که فهمیدی عاشق من شدی، کی بود؟",
    "چه چیزی در رابطه‌مون بیشتر از همه تو رو خوشحال می‌کنه؟",
    "بزرگترین آرزوت برای آینده‌مون چیه؟",
    "چه چیزی در من باعث میشه که دوستم داشته باشی؟",
    "اگه فقط یک روز از زندگیمون مونده بود، دوست داشتی چطور بگذرونیمش؟",
    "یک خاطره‌ای که از من داری و هیچوقت فراموش نمی‌کنی چیه؟",
    "چیزی هست که می‌خوای من تغییرش بدم؟",
    "در مورد من چه چیزی رو بیشتر از همه دوست داری؟",
    "تا حالا فکر کردی که رابطه‌مون به پایان برسه؟ چرا؟",
    "چه چیزی باعث میشه که تو این رابطه احساس امنیت کنی؟",
    "بزرگترین امیدت برای آینده ما چیه؟",
    "چه کاری می‌تونم انجام بدم که رابطه‌مون رو بهتر کنه؟",
    "چیزی هست که ازش می‌ترسی ولی نتونستی به من بگی؟",
    "اگر می‌تونستی یک روز کامل با من بگذرونی، دوست داشتی چیکار کنیم؟",
    "از کدوم عادت‌های من خوشت نمیاد؟",
    "اولین چیزی که در مورد من توجهت رو جلب کرد چی بود؟",
    
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
    "چه کسی در زندگیت بیشترین تاثیر رو روی شخصیتت گذاشته؟",
    "بدترین دروغی که تا حالا به من گفتی چی بوده؟",
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
    "بزرگترین زخم روحی‌ای که داری چیه؟",
    "کدوم تجربه زندگیت بیشتر از همه روت تأثیر گذاشته؟",
    "چه چیزی باعث میشه وقتی تنهایی گریه کنی؟",
    "از چی بیشتر از همه خجالت می‌کشی؟",
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
    "سه چیزی که دوست داری قبل از مرگت انجام بدی چیه؟",
    "اگر پول مشکل نبود، کجا زندگی می‌کردی؟",
    "اگه می‌تونستی هر چیزی رو در دنیا تغییر بدی، چی رو انتخاب می‌کردی؟",
    "اگه می‌تونستی با یه شخصیت مشهور شام بری، کی رو انتخاب می‌کردی؟",
    "اگه قرار بود فقط یک وسیله رو به یه جزیره متروک ببری، چی انتخاب می‌کردی؟",
    "جسورانه‌ترین کاری که تا حالا انجام دادی چی بوده؟",
    "اگه می‌تونستی یه اختراع انجام بدی، چی اختراع می‌کردی؟",
    "اگه یه ماه وقت آزاد داشتی، چیکار می‌کردی؟",
    "بهترین روز زندگیت چطور می‌گذشت؟",
    "اگه می‌تونستی با هر کسی ملاقات کنی، کی رو انتخاب می‌کردی؟",
    "اگه می‌تونستی توی هر دوره‌ای از تاریخ زندگی کنی، کدوم دوره رو انتخاب می‌کردی؟",
    "اگه یه میلیارد تومن بهت بدن، با اولین صد میلیونش چیکار می‌کنی؟",
    "خطرناک‌ترین کاری که حاضری انجام بدی چیه؟",
    
    # سوالات در مورد احساسات عمیق
    "چه موقع‌هایی بیشتر احساس تنهایی می‌کنی، حتی وقتی با منی؟",
    "عمیق‌ترین ترسی که داری چیه و چرا؟",
    "کدوم احساس رو سخت‌تر از همه می‌تونی ابراز کنی؟",
    "چه چیزی باعث میشه که احساس کنی دوست داشته نمیشی؟",
    "از چه چیزی بیشتر از همه خجالت می‌کشی؟",
    "آخرین باری که گریه کردی کِی بود و برای چی؟",
    "چه چیزی باعث میشه نسبت به من احساس ناامنی کنی؟",
    "چطور می‌تونم وقتی ناراحتی، بهتر بهت کمک کنم؟",
    "چه کاری میتونم انجام بدم که بیشتر احساس کنی دوستت دارم؟",
    "چه چیزی باعث میشه احساس کنی که واقعاً زنده‌ای؟",
    "بزرگترین نگرانیت در مورد آینده چیه؟",
    "چه موقع‌هایی احساس آرامش می‌کنی؟",
    "چه کاری من انجام میدم که ناخودآگاه اذیتت می‌کنه؟",
    "بزرگترین دلیلی که باعث میشه بخوای با من بمونی چیه؟",
    "چیزی هست که دوست داشته باشی بیشتر از من بشنوی؟",
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
    "اگه یکی از ما باید از شهر دیگه‌ای کار کنه، چطور رابطه‌مون رو مدیریت می‌کنیم؟",
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
    "چه کتابی خوندی که زندگیت رو تغییر داده؟",
    "چطور می‌تونم در جهت رشد شخصیت بهت کمک کنم؟",
    "از نظر معنوی، چه تجربه‌ای برات مهم بوده؟",
    "چه چیزی تو زندگیت می‌خوای بیشتر داشته باشی؟",
    "از نظر احساسی، کدوم بخش از شخصیتت رو می‌خوای بهبود بدی؟"
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
    
    # بررسی آیا کاربران سوال بی‌پاسخ دارند
    cursor.execute("SELECT id, question FROM questions WHERE user_id = ? AND partner_id = ? AND answer IS NULL", (user_id, partner_id))
    unanswered_user = cursor.fetchone()
    
    cursor.execute("SELECT id, question FROM questions WHERE user_id = ? AND partner_id = ? AND answer IS NULL", (partner_id, user_id))
    unanswered_partner = cursor.fetchone()
    
    # اگر کاربر اصلی سوال بی‌پاسخ دارد، یادآوری ارسال کن
    if unanswered_user:
        question_id, previous_question = unanswered_user
        await bot.send_message(user_id, f"💬 یادآوری: شما هنوز به این سوال پاسخ نداده‌اید:\n\n{previous_question}\n\n✏️ لطفاً پاسخ خود را ارسال کنید.")
    
    # اگر پارتنر سوال بی‌پاسخ دارد، یادآوری ارسال کن
    if unanswered_partner:
        question_id, previous_question = unanswered_partner
        await bot.send_message(partner_id, f"💬 یادآوری: شما هنوز به این سوال پاسخ نداده‌اید:\n\n{previous_question}\n\n✏️ لطفاً پاسخ خود را ارسال کنید.")
    
    # اگر هر دو کاربر به سوالات قبلی پاسخ داده‌اند، سوال جدید ارسال کن
    if not unanswered_user and not unanswered_partner:
        question = random.choice(questions)
        
        # ایجاد سوال جدید برای هر دو کاربر
        cursor.execute("INSERT INTO questions (user_id, partner_id, question) VALUES (?, ?, ?)", (user_id, partner_id, question))
        question_id_1 = cursor.lastrowid
        
        cursor.execute("INSERT INTO questions (user_id, partner_id, question) VALUES (?, ?, ?)", (partner_id, user_id, question))
        question_id_2 = cursor.lastrowid
        
        conn.commit()
        
        # ارسال سوال به کاربران
        await bot.send_message(user_id, f"💬 سوال جدید: {question}\n✏️ پاسخ خود را ارسال کنید.")
        await bot.send_message(partner_id, f"💬 سوال جدید: {question}\n✏️ پاسخ خود را ارسال کنید.")
        
        # ارسال پیام به ادمین
        await bot.send_message(ADMIN_ID, f"🔔 سوال جدید به کاربران {user_id} و {partner_id} ارسال شد:\n{question}")
        
        return True
    
    return False

async def scheduled_questions():
    """ ارسال سوال هر ۲ ساعت یک بار """
    while True:
        cursor.execute("SELECT user_id, partner_id FROM users WHERE partner_id IS NOT NULL")
        pairs = cursor.fetchall()
        
        # برای جلوگیری از ارسال سوال تکراری به زوج‌ها
        processed_pairs = set()
        
        for user_id, partner_id in pairs:
            # ایجاد یک کلید منحصر به فرد برای هر زوج (با مرتب‌سازی شناسه‌ها)
            pair_key = tuple(sorted([user_id, partner_id]))
            
            # اگر این زوج قبلاً پردازش نشده‌اند، سوال را ارسال کن
            if pair_key not in processed_pairs:
                await send_question(user_id, partner_id)
                processed_pairs.add(pair_key)
        
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
