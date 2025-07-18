#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.parse
import re
import json
import requests
import gzip
import brotli
import time
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def extract_init_data(url):
    """
    استخراج initData من رابط Telegram WebApp وتحويله إلى JSON
    """
    try:
        # البحث عن tgWebAppData في الرابط
        match = re.search(r'tgWebAppData=([^&]+)', url)
        
        if not match:
            print("❌ لم يتم العثور على tgWebAppData في الرابط")
            return None
        
        # استخراج البيانات المشفرة
        encoded_data = match.group(1)
        
        # فك التشفير
        decoded_data = urllib.parse.unquote(encoded_data)
        
        # استخراج معلومات المستخدم من decoded_data
        user_match = re.search(r'user=([^&]+)', decoded_data)
        start_param_match = re.search(r'start_param=([^&]+)', decoded_data)
        
        if not user_match:
            print("❌ لم يتم العثور على بيانات المستخدم")
            return None
        
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
        
        return result
        
    except Exception as e:
        print(f"❌ حدث خطأ: {str(e)}")
        return None

def send_to_api(data):
    """
    إرسال البيانات إلى API واستخراج التوكن
    """
    try:
        # رابط API
        url = "https://api.teabank.io/user-api/"
        
        # Headers
        headers = {
            "Host": "api.teabank.io",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://app.teabank.io/",
            "Content-Type": "application/json",
            "Origin": "https://app.teabank.io",
            "DNT": "1",
            "Sec-GPC": "1",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Priority": "u=4",
            "TE": "trailers"
        }
        
        # إعداد session مع retry strategy
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # إرسال الطلب
        print("⏳ جاري إرسال البيانات إلى API...")
        response = session.post(url, json=data, headers=headers, timeout=30)
        
        # التحقق من الاستجابة
        if response.status_code == 200:
            print("✅ تم إرسال البيانات بنجاح!")
            
            # طباعة الاستجابة الخام للتشخيص
            print(f"📄 الاستجابة الخام: {response.text[:200]}...")
            
            # محاولة استخراج التوكن من الاستجابة
            try:
                response_data = response.json()
                print(f"📊 البيانات المستلمة: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                
                if "token" in response_data:
                    token = response_data["token"]
                    print(f"🔑 التوكن المستخرج: {token}")
                    print("=" * 80)
                    return token
                else:
                    print("⚠️ لم يتم العثور على التوكن في الاستجابة")
                    print("🔍 المفاتيح المتاحة:", list(response_data.keys()) if isinstance(response_data, dict) else "ليس قاموس")
                    return None
                    
            except json.JSONDecodeError as e:
                print(f"❌ خطأ في تحليل JSON: {str(e)}")
                print(f"📄 أول 500 حرف من الاستجابة: {response.text[:500]}")
                
                # محاولة إصلاح مشاكل التشفير
                try:
                    # محاولة فك التشفير بطرق مختلفة
                    clean_text = response.text.encode('utf-8').decode('utf-8', errors='ignore')
                    response_data = json.loads(clean_text)
                    
                    if "token" in response_data:
                        token = response_data["token"]
                        print(f"🔑 التوكن المستخرج (بعد الإصلاح): {token}")
                        return token
                except:
                    pass
                    
                return None
                
        else:
            print(f"❌ فشل في إرسال البيانات. كود الخطأ: {response.status_code}")
            print(f"📄 تفاصيل الخطأ: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ خطأ في الاتصال: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ حدث خطأ غير متوقع: {str(e)}")
        return None

def start_farming(init_data, token, action="status"):
    """
    إرسال طلب startFarming باستخدام التوكن والـ initData
    action يمكن أن يكون: "start", "status", "claim"
    """
    try:
        # رابط API
        url = "https://api.teabank.io/user-api/"
        
        # Headers
        headers = {
            "Host": "api.teabank.io",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://app.teabank.io/",
            "Content-Type": "application/json",
            "Origin": "https://app.teabank.io",
            "DNT": "1",
            "Sec-GPC": "1",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Priority": "u=4",
            "TE": "trailers"
        }
        
        # البيانات المرسلة
        data = {
            "task": "startFarming",
            "action": action,
            "initData": init_data,
            "token": token
        }
        
        # إعداد session مع retry strategy
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # إرسال الطلب
        print("⏳ جاري إرسال طلب startFarming...")
        response = session.post(url, json=data, headers=headers, timeout=30)
        
        # التحقق من الاستجابة
        if response.status_code == 200:
            print("✅ تم إرسال طلب startFarming بنجاح!")
            
            # طباعة الاستجابة
            try:
                # محاولة فك الضغط باستخدام طرق مختلفة
                content = response.content
                
                # محاولة فك الضغط حسب نوع الترميز
                encoding = response.headers.get('content-encoding', '').lower()
                
                try:
                    if encoding == 'br':
                        # فك ضغط Brotli
                        decompressed_content = brotli.decompress(content).decode('utf-8')
                    elif encoding == 'gzip':
                        # فك ضغط gzip
                        decompressed_content = gzip.decompress(content).decode('utf-8')
                    else:
                        # لا يوجد ضغط
                        decompressed_content = content.decode('utf-8')
                    
                    response_data = json.loads(decompressed_content)
                    print(f"📊 استجابة startFarming (مفكوكة الضغط): {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                    return response_data
                except:
                    # إذا فشل فك الضغط، نحاول JSON مباشرة
                    try:
                        response_data = response.json()
                        print(f"📊 استجابة startFarming: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                        return response_data
                    except:
                        # إذا فشل كل شيء، نطبع الاستجابة الخام
                        print(f"❌ لا يمكن تحليل الاستجابة")
                        print(f"📄 Content-Encoding: {response.headers.get('content-encoding', 'غير محدد')}")
                        print(f"📄 Content-Type: {response.headers.get('content-type', 'غير محدد')}")
                        print(f"📄 أول 100 بايت من البيانات: {content[:100]}")
                        return None
                        
            except Exception as e:
                print(f"❌ خطأ عام في تحليل البيانات: {str(e)}")
                return None
        else:
            print(f"❌ فشل في إرسال طلب startFarming. كود الخطأ: {response.status_code}")
            print(f"📄 تفاصيل الخطأ: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ خطأ في الاتصال: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ حدث خطأ غير متوقع: {str(e)}")
        return None

def get_user_water_level(init_data, token):
    """
    الحصول على مستوى الماء الحالي للمستخدم
    """
    try:
        # إرسال طلب للحصول على بيانات المستخدم
        user_data = {
            "user": {},
            "initData": init_data,
            "id": "",
            "first_name": "",
            "last_name": "",
            "photo_url": "",
            "referral": "",
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
        
        result = send_to_api(user_data)
        
        if result and "water" in result:
            return int(result.get("water", 0))
        return 0
    except:
        return 0

def automated_farming_loop(extracted_data):
    """
    الحلقة التلقائية للزراعة والحصاد
    """
    print("\n🔄 بدء الحلقة التلقائية للزراعة...")
    
    # متغيرات لتتبع حالات الفشل
    water_zero_attempts = 0
    max_water_zero_attempts = 4
    water_zero_wait_times = [6*3600, 5*3600, 3*3600, 2*3600]  # 6ه، 5ه، 3ه، 2ه
    
    cycle_count = 0
    
    while True:
        try:
            cycle_count += 1
            print(f"\n{'='*60}")
            print(f"🔄 دورة رقم {cycle_count}")
            print(f"{'='*60}")
            
            # الحصول على توكن للطلب الأول
            print("🔄 الحصول على توكن للطلب الأول...")
            token_1 = send_to_api(extracted_data)
            if not token_1:
                print("❌ فشل في الحصول على توكن للطلب الأول. إعادة المحاولة خلال 5 دقائق...")
                time.sleep(300)
                continue
            
            # الحصول على مستوى الماء
            water_level = get_user_water_level(extracted_data["initData"], token_1)
            print(f"💧 مستوى الماء الحالي: {water_level}")
            
            # التحقق من مستوى الماء
            if water_level == 0:
                if water_zero_attempts < max_water_zero_attempts:
                    wait_time = water_zero_wait_times[water_zero_attempts]
                    water_zero_attempts += 1
                    
                    print(f"⚠️ الماء = 0. محاولة {water_zero_attempts}/{max_water_zero_attempts}")
                    print(f"⏰ انتظار {wait_time//3600} ساعات...")
                    
                    wait_with_countdown(wait_time)
                    continue
                else:
                    print("❌ الماء = 0 لعدة محاولات. إعادة ضبط العداد...")
                    water_zero_attempts = 0
                    wait_with_countdown(water_zero_wait_times[0])
                    continue
            else:
                water_zero_attempts = 0
            
            # الطلب الأول: محاولة بدء الزراعة
            print("🌱 الطلب الأول: محاولة بدء الزراعة...")
            farming_result = start_farming(extracted_data["initData"], token_1, "start")
            
            # الطلب الثاني: إذا فشل بدء الزراعة، جرب التحقق من الحالة
            if not farming_result or not farming_result.get("success"):
                print("🔄 الحصول على توكن للطلب الثاني...")
                token_2 = send_to_api(extracted_data)
                
                if token_2:
                    print("⚠️ الطلب الثاني: فشل بدء الزراعة. التحقق من الحالة...")
                    farming_result = start_farming(extracted_data["initData"], token_2, "status")
                else:
                    print("❌ فشل في الحصول على توكن للطلب الثاني")
                    continue
            
            if not farming_result or not farming_result.get("success"):
                print("❌ فشل في الحصول على حالة الزراعة. إعادة المحاولة خلال 10 دقائق...")
                time.sleep(600)
                continue
            
            # استخراج معلومات التوقيت
            time_left = farming_result.get("time_left", 0)
            status = farming_result.get("status", "")
            
            print(f"📊 حالة الزراعة: {status}")
            print(f"⏰ الوقت المتبقي: {time_left} ثانية")
            
            # إذا كان الحصاد متاحاً الآن
            if status == "CAN_CLAIM" and time_left == 0:
                print("✅ الحصاد متاح الآن!")
            elif time_left > 0:
                print(f"⏰ انتظار {time_left} ثانية للحصاد...")
                wait_with_countdown(time_left)
            else:
                print("⏰ انتظار 3 ساعات (الافتراضي)...")
                wait_with_countdown(3 * 3600)
            
            # الحصول على توكن للطلب الثالث (الحصاد)
            print("\n🔄 الحصول على توكن للطلب الثالث...")
            token_3 = send_to_api(extracted_data)
            
            if not token_3:
                print("❌ فشل في الحصول على توكن للحصاد. تخطي هذه الدورة...")
                continue
            
            # الطلب الثالث: إرسال طلب الحصاد
            print("🌾 الطلب الثالث: إرسال طلب الحصاد...")
            claim_result = start_farming(extracted_data["initData"], token_3, "claim")
            
            if claim_result and claim_result.get("success"):
                print("🎉 تم الحصاد بنجاح!")
                
                # عرض النتائج
                if "claimed_amount" in claim_result:
                    print(f"💰 المبلغ المحصود: {claim_result['claimed_amount']}")
                if "claimed_amount_token" in claim_result:
                    print(f"🪙 التوكنات المحصودة: {claim_result['claimed_amount_token']}")
                if "message" in claim_result:
                    print(f"📝 الرسالة: {claim_result['message']}")
            else:
                print("❌ فشل في الحصاد.")
            
            # راحة قصيرة قبل بدء الدورة التالية
            print("\n⏸️ راحة 30 ثانية قبل الدورة التالية...")
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n🛑 تم إيقاف السكريطت بواسطة المستخدم.")
            break
        except Exception as e:
            print(f"❌ خطأ في الدورة: {str(e)}")
            print("⏰ انتظار 5 دقائق قبل إعادة المحاولة...")
            time.sleep(300)

def claim_farming_old(init_data, token):
    """
    إرسال طلب claim للحصاد باستخدام التوكن والـ initData
    """
    try:
        # رابط API
        url = "https://api.teabank.io/user-api/"
        
        # Headers
        headers = {
            "Host": "api.teabank.io",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://app.teabank.io/",
            "Content-Type": "application/json",
            "Origin": "https://app.teabank.io",
            "DNT": "1",
            "Sec-GPC": "1",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Priority": "u=4",
            "TE": "trailers"
        }
        
        # البيانات المرسلة
        data = {
            "task": "startFarming",
            "action": "claim",
            "initData": init_data,
            "token": token
        }
        
        # إعداد session مع retry strategy
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # إرسال الطلب
        print("⏳ جاري إرسال طلب claim للحصاد...")
        response = session.post(url, json=data, headers=headers, timeout=30)
        
        # التحقق من الاستجابة
        if response.status_code == 200:
            print("✅ تم إرسال طلب claim بنجاح!")
            
            # طباعة الاستجابة
            try:
                # محاولة فك الضغط باستخدام طرق مختلفة
                content = response.content
                encoding = response.headers.get('content-encoding', '').lower()
                
                try:
                    if encoding == 'br':
                        # فك ضغط Brotli
                        decompressed_content = brotli.decompress(content).decode('utf-8')
                    elif encoding == 'gzip':
                        # فك ضغط gzip
                        decompressed_content = gzip.decompress(content).decode('utf-8')
                    else:
                        # لا يوجد ضغط
                        decompressed_content = content.decode('utf-8')
                    
                    response_data = json.loads(decompressed_content)
                    print(f"📊 استجابة claim: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                    return response_data
                except:
                    # إذا فشل فك الضغط، نحاول JSON مباشرة
                    try:
                        response_data = response.json()
                        print(f"📊 استجابة claim: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                        return response_data
                    except:
                        # إذا فشل كل شيء، نطبع الاستجابة الخام
                        print(f"❌ لا يمكن تحليل الاستجابة")
                        print(f"📄 Content-Encoding: {response.headers.get('content-encoding', 'غير محدد')}")
                        print(f"📄 Content-Type: {response.headers.get('content-type', 'غير محدد')}")
                        print(f"📄 أول 100 بايت من البيانات: {content[:100]}")
                        return None
                        
            except Exception as e:
                print(f"❌ خطأ عام في تحليل البيانات: {str(e)}")
                return None
        else:
            print(f"❌ فشل في إرسال طلب claim. كود الخطأ: {response.status_code}")
            print(f"📄 تفاصيل الخطأ: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ خطأ في الاتصال: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ حدث خطأ غير متوقع: {str(e)}")
        return None

def calculate_wait_time(last_collection):
    """
    حساب الوقت المتبقي للانتظار (3 ساعات من آخر جمع)
    """
    try:
        # تحويل timestamp إلى datetime
        last_collection_time = datetime.fromtimestamp(last_collection)
        
        # إضافة 3 ساعات
        next_claim_time = last_collection_time + timedelta(hours=3)
        
        # الوقت الحالي
        current_time = datetime.now()
        
        # حساب الفرق
        time_diff = next_claim_time - current_time
        
        # إرجاع عدد الثواني المتبقية (أو 0 إذا كان الوقت قد انتهى)
        return max(0, int(time_diff.total_seconds()))
        
    except Exception as e:
        print(f"❌ خطأ في حساب الوقت: {str(e)}")
        return 0

def wait_with_countdown(seconds):
    """
    انتظار مع عداد تنازلي
    """
    if seconds <= 0:
        return
    
    print(f"⏰ انتظار {seconds} ثانية ({seconds//3600} ساعة و {(seconds%3600)//60} دقيقة)")
    
    while seconds > 0:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        print(f"\r⏰ الوقت المتبقي: {hours:02d}:{minutes:02d}:{secs:02d}", end="", flush=True)
        time.sleep(1)
        seconds -= 1
    
    print("\n✅ انتهى الانتظار! جاري المتابعة...")

def main():
    print("=" * 60)
    print("🔗 مستخرج بيانات Telegram WebApp ومرسل API")
    print("=" * 60)
    
    # طلب الرابط من المستخدم
    url = input("📎 الصق رابط Telegram WebApp هنا: ").strip()
    
    if not url:
        print("❌ يرجى إدخال رابط صحيح")
        return
    
    # استخراج البيانات
    print("\n⏳ جاري استخراج البيانات...")
    result = extract_init_data(url)
    
    if not result:
        print("❌ فشل في استخراج البيانات")
        return
    
    # عرض البيانات المستخرجة
    print("\n" + "=" * 50)
    print("📋 البيانات المستخرجة:")
    print("=" * 50)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("=" * 50)
    
    # إرسال البيانات تلقائياً
    token = send_to_api(result)
    
    if token:
        print("\n🎉 تمت العملية بنجاح!")
        print(f"🔑 التوكن الخاص بك: {token}")
        
        # بدء الحلقة التلقائية للزراعة
        print("\n" + "=" * 60)
        print("🚀 بدء النظام التلقائي للزراعة والحصاد!")
        print("⚠️ للتوقف اضغط Ctrl+C")
        print("=" * 60)
        
        # استخدام الحلقة التلقائية
        automated_farming_loop(result)
    else:
        print("\n💔 فشلت العملية في الحصول على التوكن")

if __name__ == "__main__":
    main()
