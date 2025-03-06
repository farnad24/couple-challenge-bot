# 🌟 ربات تلگرام چالش همدلی (Hamdelibot)

این ربات تلگرام به زوج‌ها امکان می‌دهد تا با یکدیگر ارتباط برقرار کنند، به چالش‌های جذاب پاسخ دهند و رابطه خود را تقویت کنند. ربات با استفاده از سیستم کد یکتا، اتصال امن و خصوصی بین دو نفر را فراهم می‌کند.

## 📋 ویژگی‌های اصلی

- **🔐 سیستم اتصال ایمن**: هر کاربر یک کد یکتا دریافت می‌کند که می‌تواند با شریک خود به اشتراک بگذارد
- **🔄 دعوتنامه اختصاصی**: امکان ارسال دعوتنامه زیبا همراه با کد اختصاصی به پارتنر
- **💬 چت خصوصی**: امکان ارسال پیام‌های متنی، تصویر، ویدیو، ویس، استیکر و ویدیو مسیج
- **❓ چالش‌های عاشقانه و عمیق**: ارسال سوالات چالشی برای عمیق‌تر کردن رابطه
- **🎯 سیستم پاسخ دوطرفه**: پاسخ‌های هر کاربر فقط پس از پاسخ دادن طرف مقابل نمایش داده می‌شود
- **⏰ زمان‌بندی هوشمند**: ارسال خودکار چالش‌ها هر ۲ ساعت
- **📢 یادآوری سوالات بی‌پاسخ**: ارسال یادآوری هر ۵ ساعت برای سوالات بی‌پاسخ
- **🔔 الزام عضویت در کانال**: بررسی عضویت کاربران در کانال تعیین‌شده
- **👨‍💻 سیستم پشتیبانی**: کاربران می‌توانند با پشتیبانی در ارتباط باشند
- **👀 داشبورد مدیریت**: ادمین می‌تواند تمام تعاملات را مشاهده و مدیریت کند

## 🛠️ قابلیت‌ها برای کاربران

### اتصال و مدیریت پارتنر
- **اتصال به پارتنر**: با استفاده از کد اختصاصی
- **ارسال دعوتنامه**: ارسال متن زیبای دعوت همراه با کد اختصاصی
- **مدیریت پارتنر**: امکان قطع ارتباط در صورت نیاز
- **مشاهده وضعیت**: نمایش وضعیت اتصال و تعداد چالش‌های پاسخ داده شده

### چالش‌های عاشقانه
- **سوالات متنوع**: بیش از ۴۰ سوال چالشی در موضوعات مختلف
- **نمایش پاسخ طرف مقابل**: پس از پاسخ دادن هر دو طرف
- **یادآوری خودکار**: برای پاسخ به سوالات بی‌پاسخ

### پشتیبانی
- **ارتباط با پشتیبانی**: امکان ارسال پیام به پشتیبانی
- **انواع مختلف مشکلات**: گزارش مشکل فنی، سوال یا پیشنهاد

## 🔧 پیش‌نیازها

- Python 3.8 یا بالاتر
- aiogram نسخه 3.x
- دسترسی به تلگرام (برای دریافت توکن ربات از BotFather)
- SQLite3 (به صورت پیش‌فرض در Python موجود است)

## 💻 نصب و راه‌اندازی

### ۱. کلون کردن مخزن

```bash
git clone https://github.com/YOUR_USERNAME/hamdelibot.git
cd hamdelibot
```

### ۲. نصب وابستگی‌ها

```bash
pip install -r requirements.txt
```

### ۳. تنظیم توکن ربات

فایل `main.py` را باز کنید و متغیرهای زیر را تنظیم کنید:

```python
TOKEN = "YOUR_BOT_TOKEN"  # توکن دریافتی از BotFather
ADMIN_ID = 123456789  # آیدی عددی مدیر را وارد کنید
REQUIRED_CHANNEL = "@YOUR_CHANNEL"  # آیدی کانال اجباری
CHANNEL_TITLE = "عنوان کانال"  # عنوان کانال برای نمایش به کاربر
```

### ۴. اجرای ربات

```bash
python main.py
```

## 📝 نحوه استفاده

### برای کاربران:

1. **شروع**: دستور `/start` را برای شروع کار با ربات ارسال کنید
2. **عضویت در کانال**: در کانال تعیین شده عضو شوید و سپس روی "بررسی مجدد عضویت" کلیک کنید
3. **دریافت کد**: کد یکتای خود را دریافت کرده و آن را برای شریک خود ارسال کنید یا از دکمه "ارسال دعوتنامه" استفاده کنید
4. **اتصال**: بر روی دکمه "اتصال به پارتنر" کلیک کنید و کد دریافتی از شریک خود را وارد کنید
5. **چالش**: به سوالات چالشی پاسخ دهید - اولین چالش بلافاصله پس از اتصال ارسال می‌شود
6. **مشاهده پاسخ‌ها**: پس از اینکه هر دو طرف به یک چالش پاسخ دادند، پاسخ‌ها برای هر دو نمایش داده می‌شود
7. **گفتگو**: پیام‌ها، تصاویر، ویدیوها و... را برای شریک خود ارسال کنید
8. **درخواست پشتیبانی**: در صورت نیاز از بخش "پشتیبانی" استفاده کنید

### برای ادمین:

1. **مدیریت**: تمام پیام‌ها و تعاملات کاربران برای ادمین ارسال می‌شود
2. **پاسخ به کاربران**: با استفاده از دستور `/reply` می‌توانید به درخواست‌های پشتیبانی پاسخ دهید
3. **نظارت**: وضعیت اتصال کاربران، پاسخ‌های آنها به چالش‌ها و پیام‌های ارسالی قابل مشاهده است

## 🗂️ ساختار دیتابیس

### جدول کاربران (users)

| فیلد | توضیح |
| --- | --- |
| user_id | شناسه یکتای کاربر |
| unique_code | کد یکتای کاربر برای اتصال |
| partner_id | شناسه پارتنر (در صورت اتصال) |
| waiting_for_code | وضعیت انتظار برای ورود کد |
| last_question_time | زمان آخرین سوال ارسال شده |
| waiting_for_support | وضعیت انتظار برای ارسال پیام پشتیبانی |

### جدول سوالات (questions)

| فیلد | توضیح |
| --- | --- |
| id | شناسه یکتای سوال |
| user_id | شناسه کاربر |
| partner_id | شناسه پارتنر |
| question | متن سوال |
| answer | پاسخ کاربر (در صورت پاسخ دادن) |
| timestamp | زمان آخرین یادآوری |

### جدول پیام‌ها (messages)

| فیلد | توضیح |
| --- | --- |
| id | شناسه یکتای پیام |
| sender_id | فرستنده پیام |
| receiver_id | گیرنده پیام |
| message | متن پیام |
| media_type | نوع رسانه (تصویر، ویدیو و...) |
| media_id | شناسه فایل رسانه |

## 🚀 ویژگی‌های برجسته

- **تنوع سوالات**: بیش از ۴۰ سوال چالشی در حوزه‌های مختلف رابطه
- **امنیت کد اختصاصی**: استفاده از کدهای تصادفی برای اتصال ایمن کاربران
- **پشتیبانی کامل از انواع رسانه**: ارسال تصویر، ویدیو، ویس، استیکر و ویدیو مسیج
- **بررسی هوشمند عضویت**: الزام عضویت در کانال برای استفاده از ربات
- **سیستم یادآوری بهینه**: یادآوری خودکار هر ۵ ساعت برای سوالات بی‌پاسخ

## 🛣️ نقشه راه آینده

- افزودن چالش‌های بیشتر و متنوع‌تر
- امکان زمان‌بندی شخصی‌سازی شده برای چالش‌ها
- سیستم امتیازدهی و دستاوردها
- افزودن قابلیت یادآوری مناسبت‌های مهم
- پشتیبانی از زبان‌های مختلف

## ⚠️ نکات مهم

- از قرار دادن توکن ربات خود در گیت‌هاب خودداری کنید
- قبل از اجرای ربات در سرور، حتماً `ADMIN_ID` را با آیدی عددی تلگرام خود جایگزین کنید
- برای اطمینان از کارکرد صحیح، از نسخه‌های پایدار aiogram استفاده کنید

## 📜 لایسنس

این پروژه تحت لایسنس MIT منتشر شده است. برای اطلاعات بیشتر به فایل LICENSE مراجعه کنید.

## 👤 سازنده

این ربات توسط [فرناد باباپور] ایجاد شده است.

برای ارتباط با من:
- تلگرام: [@farnad24]
- ایمیل: farnad24@gmail.com
- لینکدین: https://ir.linkedin.com/in/farnad-babapour-4a17ba204

---

💖 با استفاده از این ربات، به زوج‌ها کمک کنید تا ارتباط عمیق‌تری برقرار کنند! 💖 
