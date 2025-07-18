#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.parse
import re
import json
import requests
import time
from datetime import datetime, timezone

def make_request(url, start_param):
    """
    إرسال طلب GET إلى الموقع وجلب البيانات
    تم إزالة استخراج الكوكيز ومعرفات API غير المطلوبة
    """
    try:
        # تحديد URL الأساسي
        base_url = "https://app.teabank.io/"
        
        # إعداد Headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Dnt': '1',
            'Sec-Gpc': '1',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
            'Te': 'trailers'
        }
        
        # إرسال الطلب
        response = requests.get(
            base_url,
            params={'tgWebAppStartParam': start_param},
            headers=headers,
            timeout=10
        )
        
        return {
            'status_code': response.status_code,
            'content': response.text
        }
        
    except Exception as e:
        print(f"❌ خطأ في الطلب: {str(e)}")
        return None

def run_task(token, task_id, user_data):
    """
    تشغيل مهمة واحدة باستخدام الـ token
    """
    try:
        api_url = "https://api.teabank.io/tasks-api/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'Origin': 'https://app.teabank.io',
            'Dnt': '1',
            'Sec-Gpc': '1',
            'Referer': 'https://app.teabank.io/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Priority': 'u=0',
            'Te': 'trailers'
        }
        
        # استخراج initData الخام من user_data الأصلي
        json_data = json.loads(user_data)
        init_data = json_data.get('initData', '')
        
        task_data = {
            "task": "completeTask",
            "token": token,
            "taskId": task_id,
            "userData": init_data
        }
        
        print(f"📤 البيانات المرسلة للمهمة {task_id}:")
        print(f"   Token: {token[:50]}...")
        print(f"   TaskId: {task_id}")
        print(f"   UserData: {init_data[:100]}...")
        
        response = requests.post(
            api_url,
            headers=headers,
            json=task_data,
            timeout=10
        )
        
        print(f"📥 رد المهمة {task_id}: {response.status_code}")
        if response.text:
            print(f"📄 محتوى الرد: {response.text[:200]}...")
        
        return response.status_code, response.text
        
    except Exception as e:
        return None, str(e)

# تم حذف دوال الانتظار - البوت سيعمل بسرعة عالية

def check_rate_limit_error(response_text):
    """
    فحص إذا كان الرد يحتوي على خطأ rate limit
    """
    try:
        response_json = json.loads(response_text)
        return response_json.get('error') == 'You have reached the daily task limit.'
    except:
        return False

def run_tasks_range(user_data, initial_token, start_task, end_task, task_type="normal"):
    """
    تشغيل مجموعة من المهام من start_task إلى end_task
    """
    current_token = initial_token
    successful_tasks = 0
    failed_tasks = 0
    
    print(f"\n🎯 بدء تشغيل المهام من {start_task} إلى {end_task} ({task_type})")
    
    for task_id in range(start_task, end_task + 1):
        print(f"\n🎯 تشغيل المهمة رقم {task_id}...")
        
        # تشغيل المهمة
        status_code, response_text = run_task(current_token, task_id, user_data)
        
        if status_code:
            if status_code == 200:
                print(f"✅ المهمة {task_id}: نجحت ({status_code})")
                successful_tasks += 1
            elif status_code == 429 and check_rate_limit_error(response_text):
                print(f"⚡ المهمة {task_id}: rate limit - سنتخطى ونكمل")
                failed_tasks += 1
            else:
                print(f"❌ المهمة {task_id}: فشلت ({status_code})")
                failed_tasks += 1
        else:
            print(f"❌ المهمة {task_id}: خطأ في الاتصال - {response_text}")
            failed_tasks += 1
        
        # إذا لم تكن المهمة الأخيرة، احصل على token جديد
        if task_id < end_task:
            print(f"🔄 الحصول على token جديد للمهمة التالية...")
            new_api_result = register_user(user_data)
            
            if new_api_result and 'token' in new_api_result:
                current_token = new_api_result['token']
                print(f"✅ تم الحصول على token جديد")
            else:
                print(f"❌ فشل في الحصول على token جديد")
                break
        
        # انتظار قصير جداً بين المهام للسرعة
        time.sleep(0.1)
    
    return successful_tasks, failed_tasks, current_token

def run_all_tasks(user_data, initial_token):
    """
    تشغيل جميع المهام مع نظام إعادة التشغيل الذكي
    """
    print("\n" + "🎯" * 20 + " بدء تشغيل المهام الذكي " + "🎯" * 20)
    
    # تشغيل المهام من 1 إلى 257
    print("🚀 بدء تشغيل المهام من 1 إلى 257...")
    
    successful_1, failed_1, token_1 = run_tasks_range(user_data, initial_token, 1, 257, "المرحلة الأولى")
    
    print(f"\n📊 نتائج المرحلة الأولى (1-257):")
    print(f"✅ نجحت: {successful_1} مهمة")
    print(f"❌ فشلت: {failed_1} مهمة")
    
    # إعادة تشغيل المهام من 1 إلى 257 مرة أخرى
    while True:
        print("\n" + "🔄" * 20 + " إعادة تشغيل المهام " + "🔄" * 20)
        
        successful_2, failed_2, token_2 = run_tasks_range(user_data, token_1, 1, 257, "إعادة التشغيل")
        
        print(f"\n📊 نتائج إعادة التشغيل (1-257):")
        print(f"✅ نجحت: {successful_2} مهمة")
        print(f"❌ فشلت: {failed_2} مهمة")
        
        # إذا لم تفشل أي مهمة، ابدأ جولة جديدة مباشرة
        if failed_2 == 0:
            print("🎉 تم إنهاء جميع المهام بنجاح في هذه الجولة!")
            print("🚀 بدء جولة جديدة مباشرة...")
            
            # الحصول على token جديد
            new_api_result = register_user(user_data)
            if new_api_result and 'token' in new_api_result:
                token_1 = new_api_result['token']
                print("✅ تم الحصول على token جديد - بدء جولة جديدة!")
            else:
                print("❌ فشل في الحصول على token جديد")
                break
        else:
            # إذا فشلت بعض المهام، استمر في الجولة التالية مباشرة
            token_1 = token_2
            time.sleep(0.1)  # انتظار قصير جداً قبل الجولة التالية

def register_user(user_data):
    """
    إرسال بيانات المستخدم إلى API teabank.io للحصول على token
    """
    try:
        api_url = "https://api.teabank.io/user-api/"
        
        # إعداد Headers للـ API
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://app.teabank.io/',
            'Content-Type': 'application/json',
            'Origin': 'https://app.teabank.io',
            'Dnt': '1',
            'Sec-Gpc': '1',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Priority': 'u=4',
            'Te': 'trailers'
        }
        
        # تحويل البيانات إلى JSON لإرسالها
        json_data = json.loads(user_data)
        
        # إرسال الطلب
        response = requests.post(
            api_url,
            headers=headers,
            json=json_data,
            timeout=15
        )
        
        print(f"📊 رمز الاستجابة: {response.status_code}")
        print(f"📄 حجم الاستجابة: {len(response.content)} بايت")
        
        if response.status_code == 200:
            try:
                # محاولة قراءة الاستجابة كـ JSON مباشرة
                # requests يتعامل مع الضغط تلقائياً
                api_response = response.json()
                print(f"✅ تم تحليل JSON بنجاح")
                if 'token' in api_response:
                    print(f"✅ تم الحصول على token: {api_response['token'][:20]}...")
                return api_response
            except json.JSONDecodeError as e:
                print(f"❌ خطأ في تحليل JSON: {e}")
                print(f"Content-Type: {response.headers.get('Content-Type', 'غير محدد')}")
                print(f"Content-Encoding: {response.headers.get('Content-Encoding', 'غير محدد')}")
                # محاولة فك الضغط يدوياً
                try:
                    import gzip
                    import brotli
                    
                    content_encoding = response.headers.get('Content-Encoding', '')
                    if content_encoding == 'br':
                        decompressed = brotli.decompress(response.content)
                        api_response = json.loads(decompressed.decode('utf-8'))
                        print(f"✅ تم فك الضغط Brotli بنجاح")
                        return api_response
                    elif content_encoding == 'gzip':
                        decompressed = gzip.decompress(response.content)
                        api_response = json.loads(decompressed.decode('utf-8'))
                        print(f"✅ تم فك الضغط Gzip بنجاح")
                        return api_response
                    else:
                        print(f"Raw response (first 100 bytes): {response.content[:100]}")
                        return None
                except Exception as decompress_error:
                    print(f"❌ خطأ في فك الضغط: {decompress_error}")
                    return None
        else:
            print(f"❌ خطأ في API: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ خطأ في تسجيل المستخدم: {str(e)}")
        return None

def extract_init_data(url):
    """
    استخراج initData من رابط Telegram WebApp وتحويله إلى JSON
    """
    try:
        # البحث عن tgWebAppData في الرابط
        match = re.search(r'tgWebAppData=([^&]+)', url)
        
        if not match:
            print("❌ لم يتم العثور على tgWebAppData في الرابط")
            return None, None
        
        # استخراج البيانات المشفرة
        encoded_data = match.group(1)
        
        # فك التشفير
        decoded_data = urllib.parse.unquote(encoded_data)
        
        # استخراج معلومات المستخدم من decoded_data
        user_match = re.search(r'user=([^&]+)', decoded_data)
        start_param_match = re.search(r'start_param=([^&]+)', decoded_data)
        
        if not user_match:
            print("❌ لم يتم العثور على بيانات المستخدم")
            return None, None
        
        # فك تشفير بيانات المستخدم
        user_encoded = user_match.group(1)
        user_decoded = urllib.parse.unquote(user_encoded)
        
        # تحويل بيانات المستخدم إلى JSON
        user_data = json.loads(user_decoded)
        
        # استخراج referral (start_param)
        referral = start_param_match.group(1) if start_param_match else ""
        
        # بناء النتيجة النهائية
        result = {
            "user": user_data,
            "initData": decoded_data,
            "id": str(user_data.get("id", "")),
            "first_name": user_data.get("first_name", ""),
            "last_name": user_data.get("last_name", ""),
            "photo_url": user_data.get("photo_url", ""),
            "referral": referral,
            "utm_source": "",
            "utm_medium": "",
            "utm_campaign": "",
            "utm_content": "",
            "utm_term": "",
            "referrer": "",
            "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
            "tg_version": "9.0",
            "platform": "android",
            "language": "en-US",
            "task": "checkOrRegisterUser"
        }
        
        return json.dumps(result, ensure_ascii=False), referral
        
    except Exception as e:
        print(f"❌ حدث خطأ: {str(e)}")
        return None, None

def main():
    # طلب الرابط من المستخدم
    url = input("الصق الرابط هنا: ").strip()
    
    if not url:
        print("❌ يرجى إدخال رابط صحيح")
        return
    
    # استخراج initData
    result, referral = extract_init_data(url)
    
    if result:
        print()  # سطر فارغ للفصل
        print("=" * 50)
        print("النتيجة:")
        print("=" * 50)
        print(result)
        print("=" * 50)
        
        # إرسال طلب إلى الموقع (اختياري)
        print("\n🔄 جاري إرسال طلب إلى الموقع...")
        request_result = make_request(url, referral or "")
        
        if request_result:
            print("\n" + "=" * 50)
            print("بيانات الطلب:")
            print("=" * 50)
            print(f"Status Code: {request_result['status_code']}")
            print("=" * 50)
        else:
            print("❌ فشل في إرسال الطلب")
            
        # إرسال البيانات إلى API للحصول على token
        print("\n🔄 جاري تسجيل المستخدم والحصول على token...")
        api_result = register_user(result)
        
        if api_result:
            # عرض ترحيبي جميل
            first_name = api_result.get('first_name', '')
            last_name = api_result.get('last_name', '')
            water = api_result.get('water', 0)
            ton_balance = api_result.get('ton_balance', '0.000000000')
            token = api_result.get('token', '')
            
            print("\n" + "🎉" * 25)
            print(f"مرحباً يا {first_name} {last_name}!")
            print(f"💰 رصيدك الحالي: {ton_balance} TON")
            print(f"💧 معك {water} مية")
            print("🎉" * 25)
            
            print("\n" + "🔑" * 15 + " TOKEN " + "🔑" * 15)
            print(f"🔐 الـ Token الخاص بك:")
            print(f"{token}")
            print("🔑" * 37)
            
            print("\n" + "📊" * 15 + " تفاصيل إضافية " + "📊" * 15)
            print(f"🆔 ID: {api_result.get('id', 'غير متوفر')}")
            print(f"🌍 البلد: {api_result.get('country', 'غير متوفر')}")
            print(f"🏙️ المدينة: {api_result.get('city', 'غير متوفر')}")
            print(f"⚡ الطاقة: {api_result.get('energy', 0)}")
            print(f"🌳 عدد الأشجار: {api_result.get('trees_count', 0)}")
            
            if 'income' in api_result:
                income = api_result['income']
                print(f"💵 الدخل اليومي: {income.get('per_day', '0')} TON")
                print(f"⏰ الدخل بالساعة: {income.get('per_hour', '0')} TON")
            
            print("📊" * 47)
            
            # طباعة الـ response الكامل للمطورين
            print("\n" + "=" * 50)
            print("الاستجابة الكاملة (للمطورين):")
            print("=" * 50)
            print(json.dumps(api_result, ensure_ascii=False, indent=2))
            print("=" * 50)
            
            # بدء تشغيل المهام من 1 إلى 257
            print("\n" + "🎯" * 20 + " بدء تشغيل المهام " + "🎯" * 20)
            run_all_tasks(result, api_result.get('token'))
                
        else:
            print("❌ فشل في تسجيل المستخدم")
    
    # رسالة في حالة عدم وجود referral parameter - مجرد تحذير وليس خطأ
    if not referral:
        print("⚠️ لم يتم العثور على referral parameter، لكن سيتم المتابعة بدونه...")

if __name__ == "__main__":
    main()