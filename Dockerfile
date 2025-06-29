# پایه تصویر پایتون 3.11 slim (کم حجم و مناسب)
FROM python:3.11-slim

# دایرکتوری کاری داخل کانتینر
WORKDIR /app

# کپی فایل requirements.txt به دایرکتوری کاری
COPY requirements.txt .

# نصب پکیج‌ها بدون کش برای صرفه‌جویی در حجم
RUN pip install --no-cache-dir -r requirements.txt

# کپی کل کد پروژه به دایرکتوری کاری
COPY . .

# فرمان شروع اجرای ربات
CMD ["python", "main.py"]
