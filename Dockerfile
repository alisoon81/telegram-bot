# از ایمیج رسمی پایتون استفاده کن
FROM python:3.11-slim

# محل کار داخل کانتینر
WORKDIR /app

# فایل‌های پروژه رو کپی کن
COPY . .

# نصب وابستگی‌ها
RUN pip install --no-cache-dir -r requirements.txt

# پورت مورد استفاده (برای Flask مثلاً 8080)
EXPOSE 8080

# اجرای ربات
CMD ["python", "main.py"]
