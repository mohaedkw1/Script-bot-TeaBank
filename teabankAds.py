#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.parse
import re
import json
import requests
import time
import sys

class TeaBankAutomation:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Dnt': '1',
            'Sec-Gpc': '1'
        })
        # التأكد من أن requests تفك الضغط تلقائياً
        self.session.headers['Accept-Encoding'] = 'gzip, deflate, br'
        self.current_token = None
        self.user_data = None
        self.init_data = None
        self.signature = None
        
    def extract_init_data(self, url):
        """
        استخراج initData من رابط Telegram WebApp وتحويله إلى JSON
        """
        try:
            print("🔄 استخراج البيانات من الرابط...")
            
            # البحث عن tgWebAppData في الرابط
            match = re.search(r'tgWebAppData=([^&]+)', url)
            
            if not match:
                print("❌ لم يتم العثور على tgWebAppData في الرابط")
                return False
            
            # استخراج البيانات المشفرة
            encoded_data = match.group(1)
            
            # فك التشفير
            decoded_data = urllib.parse.unquote(encoded_data)
            self.init_data = decoded_data
            
            # استخراج معلومات المستخدم من decoded_data
            user_match = re.search(r'user=([^&]+)', decoded_data)
            start_param_match = re.search(r'start_param=([^&]+)', decoded_data)
            
            if not user_match:
                print("❌ لم يتم العثور على بيانات المستخدم")
                return False
            
            # فك تشفير بيانات المستخدم
            user_encoded = user_match.group(1)
            user_decoded = urllib.parse.unquote(user_encoded)
            
            # تحويل بيانات المستخدم إلى JSON
            self.user_data = json.loads(user_decoded)
            
            # استخراج referral (start_param)
            referral = start_param_match.group(1) if start_param_match else ""
            
            # استخراج signature من البيانات المفكوكة
            signature_match = re.search(r'signature=([^&]+)', decoded_data)
            if signature_match:
                self.signature = signature_match.group(1)
                print(f"✅ تم استخراج signature: {self.signature[:50]}...")
            else:
                print("⚠️ لم يتم العثور على signature في البيانات")
            
            print(f"✅ تم استخراج بيانات المستخدم: {self.user_data.get('first_name', '')} {self.user_data.get('last_name', '')}")
            print(f"📊 معرف المستخدم: {self.user_data.get('id', '')}")
            print(f"📊 طول initData: {len(self.init_data)}")
            return True
            
        except Exception as e:
            print(f"❌ حدث خطأ في استخراج البيانات: {str(e)}")
            return False

    def step1_register_user(self):
        """
        الخطوة الأولى: تسجيل/فحص المستخدم في TeaBank
        """
        try:
            print("\n🔄 الخطوة 1: تسجيل/فحص المستخدم...")
            
            url = "https://api.teabank.io/user-api/"
            
            payload = {
                "user": self.user_data,
                "initData": self.init_data,
                "id": str(self.user_data.get("id", "")),
                "first_name": self.user_data.get("first_name", ""),
                "last_name": self.user_data.get("last_name", ""),
                "photo_url": self.user_data.get("photo_url", ""),
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
            
            headers = {
                'Content-Type': 'application/json',
                'Referer': 'https://app.teabank.io/',
                'Origin': 'https://app.teabank.io',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'Priority': 'u=4',
                'Te': 'trailers'
            }
            
            response = self.session.post(url, json=payload, headers=headers)
            
            print(f"📊 رمز الحالة: {response.status_code}")
            print(f"📊 حجم الرد: {len(response.content)} bytes")
            print(f"📊 ترويسات الرد: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    # محاولة فك ضغط البيانات يدوياً إذا لزم الأمر
                    content_encoding = response.headers.get('content-encoding')
                    
                    if content_encoding == 'br':
                        # فك ضغط Brotli
                        try:
                            import brotli
                            decompressed_content = brotli.decompress(response.content)
                            response_text = decompressed_content.decode('utf-8')
                            print(f"📊 تم فك ضغط Brotli بنجاح: {response_text[:200]}...")
                            data = json.loads(response_text)
                        except ImportError:
                            print("⚠️ مكتبة brotli غير متوفرة. محاولة استخدام response.text العادي...")
                            data = response.json()
                        except Exception as e:
                            print(f"⚠️ فشل فك ضغط Brotli: {e}. محاولة استخدام response.text العادي...")
                            data = response.json()
                    elif content_encoding in ['gzip', 'deflate']:
                        # فك ضغط gzip/deflate
                        import gzip
                        try:
                            decompressed_content = gzip.decompress(response.content)
                            response_text = decompressed_content.decode('utf-8')
                            print(f"📊 تم فك ضغط gzip بنجاح: {response_text[:200]}...")
                            data = json.loads(response_text)
                        except:
                            # إذا فشل فك الضغط، استخدم response.text العادي
                            data = response.json()
                    else:
                        data = response.json()
                    
                    if 'token' in data:
                        self.current_token = data['token']
                        print(f"✅ تم الحصول على التوكن الأول: {self.current_token[:50]}...")
                        return True
                    else:
                        print("❌ لم يتم العثور على التوكن في الرد")
                        print(f"📊 محتوى JSON: {data}")
                        return False
                except json.JSONDecodeError as e:
                    print(f"❌ خطأ في تحليل JSON: {str(e)}")
                    print(f"📊 محتوى الرد الخام: {response.content[:500]}")
                    return False
                except Exception as e:
                    print(f"❌ خطأ عام: {str(e)}")
                    return False
            else:
                print(f"❌ فشل في الطلب الأول. رمز الحالة: {response.status_code}")
                print(f"📊 محتوى الرد: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ خطأ في الخطوة 1: {str(e)}")
            return False

    def step2_get_user_data(self):
        """
        الخطوة الثانية: الحصول على بيانات المستخدم وتحديث التوكن
        """
        try:
            print("\n🔄 الخطوة 2: الحصول على بيانات المستخدم...")
            
            url = "https://api.teabank.io/user-api/"
            
            payload = {
                "task": "getUserData",
                "token": self.current_token
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Referer': 'https://app.teabank.io/',
                'Origin': 'https://app.teabank.io',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'Priority': 'u=4',
                'Te': 'trailers'
            }
            
            response = self.session.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if 'token' in data:
                    self.current_token = data['token']
                    print(f"✅ تم تحديث التوكن: {self.current_token[:50]}...")
                    return True
                else:
                    print("❌ لم يتم العثور على التوكن المحدث في الرد")
                    return False
            else:
                print(f"❌ فشل في الطلب الثاني. رمز الحالة: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ خطأ في الخطوة 2: {str(e)}")
            return False

    def step3_get_advertisement(self):
        """
        الخطوة الثالثة: الحصول على إعلان من Adsgram
        """
        try:
            print("\n🔄 الخطوة 3: الحصول على إعلان...")
            
            if not self.signature:
                print("❌ لا يوجد signature متاح")
                return False
            
            # إنشاء data_check_string بالتنسيق الصحيح (Base64)
            import urllib.parse
            import base64
            import time
            import random
            
            # فك تشفير البيانات وإعادة تكوينها بالشكل الصحيح
            parts = self.init_data.split('&')
            data_parts = {}
            for part in parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    data_parts[key] = urllib.parse.unquote(value)
            
            # تحويل user data إلى JSON عادي (بدون URL encoding)
            user_json = data_parts.get('user', '{}')
            
            # بناء النص للـ Base64
            data_check_text = f"auth_date={data_parts.get('auth_date', '')}\nquery_id={data_parts.get('query_id', '')}\nuser={user_json}"
            
            # تحويل إلى Base64
            data_check_base64 = base64.b64encode(data_check_text.encode('utf-8')).decode('utf-8')
            
            # إنشاء معاملات إضافية
            tg_id = self.user_data.get('id', '')
            request_id = str(random.randint(10**19, 10**20-1))
            raw_hash = f"{data_check_text}sdk_version=1.25.1tg_id={tg_id}tg_platform=androidtma_version=9.0request_id={request_id}"
            import hashlib
            raw = hashlib.sha256(raw_hash.encode()).hexdigest()
            
            print(f"📊 data_check_base64: {data_check_base64[:100]}...")
            
            url = f"https://api.adsgram.ai/adv?envType=telegram&blockId=7558&platform=Linux+x86_64&language=ar&top_domain=app.teabank.io&signature={self.signature}&data_check_string={data_check_base64}&sdk_version=1.25.1&tg_id={tg_id}&tg_platform=android&tma_version=9.0&request_id={request_id}&raw={raw}"
            
            headers = {
                'Referer': 'https://app.teabank.io/',
                'X-Color-Scheme': 'dark',
                'X-Is-Fullscreen': 'false',
                'Origin': 'https://app.teabank.io',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
                'Priority': 'u=4',
                'Cache-Control': 'max-age=0',
                'Te': 'trailers',
                'Connection': 'keep-alive'
            }
            
            print(f"📊 URL المرسل: {url}")
            
            response = self.session.get(url, headers=headers)
            
            print(f"📊 رمز الحالة Adsgram: {response.status_code}")
            print(f"📊 محتوى رد Adsgram: {response.text[:300]}...")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ تم الحصول على بيانات الإعلان")
                
                # البحث عن الرابط الذي يحتوي على &type=render&trackingtypeid=13
                response_text = response.text
                
                # البحث عن أول رابط يحتوي على النمط المطلوب
                pattern = r'https://api\.adsgram\.ai/event\?record=([^"&]+)&type=render&trackingtypeid=13'
                matches = re.findall(pattern, response_text)
                
                if matches:
                    self.event_record = matches[0]  # أخذ أول match
                    print(f"✅ تم استخراج event record من &type=render&trackingtypeid=13: {self.event_record[:50]}...")
                    return True
                else:
                    print("❌ لم يتم العثور على رابط يحتوي على &type=render&trackingtypeid=13")
                    print(f"📊 محتوى الرد للفحص: {response_text[:1000]}...")
                    
                    # محاولة بديلة - البحث عن أي event URL
                    fallback_urls = re.findall(r'https://api\.adsgram\.ai/event\?record=([^"&]+)', response_text)
                    if fallback_urls:
                        print(f"🔍 تم العثور على {len(fallback_urls)} روابط event بديلة")
                        for i, url in enumerate(fallback_urls[:3]):
                            print(f"   {i+1}: {url[:80]}...")
                    return False
            else:
                print(f"❌ فشل في الطلب الثالث. رمز الحالة: {response.status_code}")
                if response.status_code == 400 and "Session too old" in response.text:
                    print("⚠️ الرابط قديم! تحتاج لرابط Telegram WebApp جديد وحديث.")
                    print("💡 احصل على رابط جديد من تطبيق TeaBank في Telegram وجرب مرة أخرى.")
                print(f"📊 ترويسات الرد: {dict(response.headers)}")
                print(f"📊 محتوى الخطأ: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ خطأ في الخطوة 3: {str(e)}")
            return False

    def step4_track_event(self):
        """
        الخطوة الرابعة: تتبع حدث المكافأة
        """
        if not self.event_record:
            print("❌ لا يوجد event record متاح")
            return False
            
        try:
            print("\n🔄 الخطوة 4: تتبع حدث المكافأة...")
            
            url = f"https://api.adsgram.ai/event?record={self.event_record}&type=reward&trackingtypeid=14"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://app.teabank.io/',
                'Origin': 'https://app.teabank.io',
                'DNT': '1',
                'Sec-GPC': '1',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
                'Priority': 'u=4',
                'Cache-Control': 'max-age=0',
                'Te': 'trailers',
                'Connection': 'keep-alive'
            }
            
            response = self.session.get(url, headers=headers, timeout=30)
            print(f"📊 رمز الحالة: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ تم تتبع حدث المكافأة بنجاح")
                return True
            else:
                print(f"❌ فشل في تتبع حدث المكافأة. رمز الحالة: {response.status_code}")
                print(f"📊 محتوى الخطأ: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ خطأ في الخطوة 4: {str(e)}")
            return False

    def step5_get_final_user_data(self):
        """
        الخطوة الخامسة: طلب getUserData النهائي بعد الإعلان
        """
        try:
            print("\n🔄 الخطوة 5: الحصول على بيانات المستخدم النهائية...")
            
            url = "https://api.teabank.io/user-api/"
            
            payload = {
                "task": "getUserData",
                "token": self.current_token
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://app.teabank.io/',
                'Content-Type': 'application/json',
                'Origin': 'https://app.teabank.io',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'Priority': 'u=4',
                'Te': 'trailers'
            }
            
            response = self.session.post(url, json=payload, headers=headers, timeout=30)
            print(f"📊 رمز الحالة: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print("✅ تم الحصول على بيانات المستخدم النهائية بنجاح")
                    
                    # عرض النتائج المهمة
                    if 'balance' in data:
                        print(f"💰 الرصيد: {data['balance']}")
                    
                    if 'energy' in data:
                        print(f"⚡ الطاقة: {data['energy']}")
                        
                    if 'token' in data:
                        self.current_token = data['token']
                        print(f"🔑 تم تحديث التوكن النهائي")
                        
                    return True
                    
                except:
                    # في حالة عدم نجاح JSON parsing، نعيد المحاولة مع الطلب الأول
                    print("⚠️ مشكلة في قراءة البيانات، جاري إعادة المحاولة...")
                    return self.retry_with_initial_request()
            else:
                print(f"❌ فشل في الحصول على البيانات. رمز الحالة: {response.status_code}")
                print(f"📊 محتوى الخطأ: {response.text}")
                
                # إعادة المحاولة مع الطلب الأول
                print("🔄 جاري إعادة المحاولة مع تسجيل جديد...")
                return self.retry_with_initial_request()
                
        except Exception as e:
            print(f"❌ خطأ في الخطوة 5: {str(e)}")
            print("🔄 جاري إعادة المحاولة مع تسجيل جديد...")
            return self.retry_with_initial_request()
    
    def retry_with_initial_request(self):
        """
        إعادة المحاولة مع الطلب الأول للحصول على توكن جديد
        """
        try:
            print("🔄 إعادة تشغيل الطلب الأول للحصول على توكن جديد...")
            
            if self.step1_register_user():
                print("✅ تم تجديد التوكن، جاري المحاولة مرة أخرى...")
                
                # محاولة getUserData مرة أخرى
                url = "https://api.teabank.io/user-api/"
                payload = {
                    "task": "getUserData", 
                    "token": self.current_token
                }
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Referer': 'https://app.teabank.io/',
                    'Content-Type': 'application/json',
                    'Origin': 'https://app.teabank.io',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-site',
                    'Priority': 'u=4',
                    'Te': 'trailers'
                }
                
                response = self.session.post(url, json=payload, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ تم الحصول على البيانات النهائية بنجاح بعد إعادة المحاولة")
                    
                    # عرض النتائج
                    if 'balance' in data:
                        print(f"💰 الرصيد: {data['balance']}")
                    if 'energy' in data:
                        print(f"⚡ الطاقة: {data['energy']}")
                        
                    return True
                else:
                    print(f"❌ فشلت إعادة المحاولة. رمز الحالة: {response.status_code}")
                    return False
            else:
                print("❌ فشل في تجديد التوكن")
                return False
                
        except Exception as e:
            print(f"❌ خطأ في إعادة المحاولة: {str(e)}")
            return False



    def run_automation(self, telegram_url):
        """
        تشغيل العملية الكاملة
        """
        print("🚀 بدء عملية أتمتة TeaBank...")
        print("=" * 60)
        
        # استخراج البيانات من الرابط
        if not self.extract_init_data(telegram_url):
            print("❌ فشل في استخراج البيانات من الرابط")
            return False
        
        # تأخير قصير
        time.sleep(1)
        
        # تنفيذ الخطوات بالتسلسل
        steps = [
            self.step1_register_user,
            self.step2_get_user_data,
            self.step3_get_advertisement,
            self.step4_track_event,
            self.step5_get_final_user_data
        ]
        
        for i, step in enumerate(steps, 1):
            if not step():
                print(f"\n❌ فشل في الخطوة {i}. توقف التنفيذ.")
                return False
            
            # تأخير بين الخطوات
            if i < len(steps):
                time.sleep(2)
        
        print("\n" + "=" * 60)
        print("🎉 تم إكمال جميع الخطوات بنجاح!")
        print("=" * 60)
        return True

def main():
    """
    الدالة الرئيسية مع التشغيل المستمر التلقائي
    """
    print("🤖 أتمتة TeaBank - إصدار 1.0")
    print("=" * 60)
    
    # طلب الرابط من المستخدم
    url = input("الصق رابط Telegram WebApp هنا: ").strip()
    
    if not url:
        print("❌ يرجى إدخال رابط صحيح")
        return
    
    # فاصل زمني ثابت 30 دقيقة
    interval = 30
    
    print(f"\n🔄 سيتم تشغيل العملية كل {interval} دقيقة تلقائياً")
    print("⏹️ اضغط Ctrl+C لإيقاف التشغيل")
    print("=" * 60)
    
    cycle_count = 0
    success_count = 0
    
    try:
        while True:
            cycle_count += 1
            print(f"\n🚀 بدء الدورة رقم {cycle_count}")
            print(f"⏰ الوقت: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 40)
            
            # إنشاء كائن أتمتة جديد لكل دورة
            automation = TeaBankAutomation()
            
            try:
                success = automation.run_automation(url)
                
                if success:
                    success_count += 1
                    print(f"\n✅ الدورة {cycle_count} تمت بنجاح!")
                else:
                    print(f"\n⚠️ الدورة {cycle_count} فشلت، سيتم المحاولة في الدورة التالية")
                    
            except Exception as e:
                print(f"\n❌ خطأ في الدورة {cycle_count}: {str(e)}")
            
            # إحصائيات
            success_rate = (success_count / cycle_count) * 100
            print(f"\n📊 إحصائيات:")
            print(f"   • إجمالي الدورات: {cycle_count}")
            print(f"   • الدورات الناجحة: {success_count}")
            print(f"   • معدل النجاح: {success_rate:.1f}%")
            
            # انتظار الفاصل الزمني
            print(f"\n⏳ انتظار {interval} دقيقة قبل الدورة التالية...")
            print("=" * 60)
            
            # انتظار مع عداد تنازلي
            for i in range(interval * 60):
                time.sleep(1)
                if i % 300 == 0 and i > 0:  # كل 5 دقائق
                    remaining_minutes = interval - (i // 60)
                    print(f"⏱️ متبقي {remaining_minutes} دقيقة...")
                    
    except KeyboardInterrupt:
        print(f"\n\n⏹️ تم إيقاف التشغيل المستمر")
        print(f"📊 إحصائيات نهائية:")
        print(f"   • إجمالي الدورات: {cycle_count}")
        print(f"   • الدورات الناجحة: {success_count}")
        if cycle_count > 0:
            print(f"   • معدل النجاح: {(success_count/cycle_count)*100:.1f}%")
        print("👋 شكراً لاستخدام أتمتة TeaBank!")
    except Exception as e:
        print(f"\n❌ خطأ عام في التشغيل المستمر: {str(e)}")

if __name__ == "__main__":
    main()
