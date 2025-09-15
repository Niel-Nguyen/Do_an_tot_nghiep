#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script kiểm tra Google API Key (Gemini)
"""

import os
import requests
import json
from dotenv import load_dotenv

def load_api_key():
    """Load API key từ .env file"""
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Không tìm thấy GOOGLE_API_KEY trong file .env")
        return None
    
    print(f"✅ Đã load API key: {api_key[:10]}...{api_key[-4:]}")
    return api_key

def check_api_key_basic(api_key):
    """Kiểm tra cơ bản API key format"""
    if not api_key:
        return False
    
    if not api_key.startswith('AIza'):
        print("❌ API key không đúng format (phải bắt đầu với 'AIza')")
        return False
    
    if len(api_key) != 39:
        print(f"⚠️  API key có độ dài {len(api_key)}, thường là 39 ký tự")
    
    print("✅ API key có format hợp lệ")
    return True

def test_embedding_api(api_key):
    """Kiểm tra API key với embedding API"""
    print("🔄 Đang kiểm tra API key với Embedding...")
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent"
    
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': api_key
    }
    
    data = {
        "model": "models/embedding-001",
        "content": {
            "parts": [{
                "text": "Test embedding để kiểm tra quota"
            }]
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if 'embedding' in result:
                embedding_values = result['embedding']['values']
                print(f"✅ Embedding API hoạt động! Vector dimension: {len(embedding_values)}")
                return True
            else:
                print(f"⚠️  Embedding response không đúng format: {result}")
                return False
        elif response.status_code == 429:
            error_detail = response.json()
            print(f"❌ Embedding API đã hết quota: {error_detail}")
            return False
        elif response.status_code == 403:
            print("❌ Embedding API bị từ chối (có thể đã hết quota hoặc bị disable)")
            return False
        else:
            print(f"❌ Embedding API error: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout khi gọi Embedding API (có thể do mạng chậm)")
        return False
    except Exception as e:
        print(f"❌ Lỗi khi test Embedding API: {e}")
        return False

def test_gemini_api(api_key):
    """Kiểm tra API key bằng cách gọi Gemini API"""
    print("🔄 Đang kiểm tra API key với Gemini...")
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': api_key
    }
    
    data = {
        "contents": [{
            "parts": [{
                "text": "Explain how AI works in a few words"
            }]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result:
                content = result['candidates'][0]['content']['parts'][0]['text']
                print(f"✅ API key hoạt động! Response: {content[:50]}...")
                return True
            else:
                print(f"⚠️  API response không đúng format: {result}")
                return False
        elif response.status_code == 400:
            error_detail = response.json()
            print(f"❌ API key không hợp lệ: {error_detail}")
            return False
        elif response.status_code == 403:
            print("❌ API key bị từ chối (có thể đã hết quota hoặc bị disable)")
            return False
        else:
            print(f"❌ API error: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout khi gọi API (có thể do mạng chậm)")
        return False
    except Exception as e:
        print(f"❌ Lỗi khi test API: {e}")
        return False

def list_available_models(api_key):
    """Liệt kê các model có sẵn"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    try:
        print("🔄 Đang lấy danh sách models...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            models = result.get('models', [])
            
            print(f"✅ Tìm thấy {len(models)} models:")
            gemini_models = []
            for model in models:
                model_name = model.get('name', '')
                if 'gemini' in model_name.lower():
                    display_name = model.get('displayName', model_name)
                    gemini_models.append((model_name, display_name))
            
            if gemini_models:
                print("\n🤖 Gemini Models:")
                for name, display in sorted(gemini_models):
                    if 'generateContent' in model.get('supportedGenerationMethods', []):
                        status = "✅ Hỗ trợ generateContent"
                    else:
                        status = "❌ Không hỗ trợ generateContent"
                    print(f"   - {display} ({name.split('/')[-1]}) - {status}")
            
            return True
        else:
            print(f"❌ Không thể lấy danh sách models: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi khi lấy models: {e}")
        return False

def check_api_usage(api_key):
    """Kiểm tra usage của API key bằng cách gọi multiple requests"""
    print("\n📊 Kiểm tra API Usage...")
    
    test_requests = [
        "Xin chào",
        "Bạn có khỏe không?",
        "Hôm nay thời tiết thế nào?",
        "Cảm ơn bạn",
        "Tạm biệt"
    ]
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': api_key
    }
    
    success_count = 0
    error_count = 0
    rate_limit_count = 0
    
    print(f"🔄 Đang test {len(test_requests)} requests để kiểm tra usage...")
    
    for i, test_text in enumerate(test_requests, 1):
        data = {
            "contents": [{
                "parts": [{"text": test_text}]
            }]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=5)
            
            if response.status_code == 200:
                success_count += 1
                print(f"  ✅ Request {i}/5: Thành công")
            elif response.status_code == 429:
                rate_limit_count += 1
                print(f"  ⚠️  Request {i}/5: Rate limit (429)")
                # Thêm delay khi gặp rate limit
                import time
                time.sleep(1)
            elif response.status_code == 403:
                error_count += 1
                error_detail = response.json()
                print(f"  ❌ Request {i}/5: Quota exceeded hoặc API disabled")
                print(f"     Chi tiết: {error_detail.get('error', {}).get('message', 'Unknown error')}")
                break  # Dừng test nếu quota hết
            else:
                error_count += 1
                print(f"  ❌ Request {i}/5: Error {response.status_code}")
            
            # Delay nhỏ giữa các requests
            import time
            time.sleep(0.5)
            
        except Exception as e:
            error_count += 1
            print(f"  ❌ Request {i}/5: Exception - {e}")
    
    # Tổng kết
    print(f"\n📈 Kết quả Usage Test:")
    print(f"   ✅ Thành công: {success_count}/5")
    print(f"   ⚠️  Rate limit: {rate_limit_count}/5")
    print(f"   ❌ Lỗi: {error_count}/5")
    
    if success_count == 5:
        print("   🎉 API hoạt động tốt, không có vấn đề về quota!")
    elif success_count > 0:
        print("   ⚠️  API hoạt động nhưng có một số vấn đề")
    else:
        print("   ❌ API không hoạt động hoặc đã hết quota")
    
    return success_count > 0

def get_quota_info(api_key):
    """Lấy thông tin quota từ các endpoint khác"""
    print("\n💳 Thông tin Quota & Billing:")
    
    # Thử gọi API với invalid request để xem error message
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': api_key
    }
    
    # Request với token limit cao để trigger quota info
    large_text = "Hãy viết một câu chuyện dài về " * 1000  # Tạo text dài
    data = {
        "contents": [{
            "parts": [{"text": large_text}]
        }],
        "generationConfig": {
            "maxOutputTokens": 8192  # Max tokens
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 429:
            error_detail = response.json()
            print("   ⚠️  Rate limit detected:")
            print(f"      Message: {error_detail.get('error', {}).get('message', 'No details')}")
        elif response.status_code == 400:
            error_detail = response.json()
            if 'quota' in str(error_detail).lower():
                print("   📊 Quota information found in error:")
                print(f"      {error_detail.get('error', {}).get('message', 'No details')}")
        
    except Exception as e:
        print(f"   ℹ️  Không thể lấy thông tin quota chi tiết: {e}")
    
    print("\n🔗 Links hữu ích:")
    print("   • AI Studio: https://aistudio.google.com/app/apikey")
    print("   • Cloud Console Quotas: https://console.cloud.google.com/iam-admin/quotas")
    print("   • Billing: https://console.cloud.google.com/billing")

def check_api_quotas(api_key):
    """Kiểm tra quota và usage của API key"""
    # Gọi các hàm kiểm tra usage
    check_api_usage(api_key)
    get_quota_info(api_key)

def test_embedding_api(api_key):
    """Kiểm tra API key với Embedding API (dùng cho RAG)"""
    print("🔄 Đang kiểm tra Embedding API...")
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"
    
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': api_key
    }
    
    data = {
        "content": {
            "parts": [{
                "text": "Test embedding for Vietnamese restaurant dishes"
            }]
        },
        "taskType": "RETRIEVAL_DOCUMENT"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if 'embedding' in result:
                embedding_length = len(result['embedding']['values'])
                print(f"✅ Embedding API hoạt động! Vector dimension: {embedding_length}")
                return True
            else:
                print(f"⚠️  Embedding API response không đúng format: {result}")
                return False
        elif response.status_code == 429:
            error_detail = response.json()
            print(f"❌ EMBEDDING API HẾT QUOTA: {error_detail}")
            print("   📊 Chi tiết quota violations:")
            if 'error' in error_detail and 'details' in error_detail['error']:
                for detail in error_detail['error']['details']:
                    if 'violations' in detail:
                        for violation in detail['violations']:
                            quota_metric = violation.get('quota_metric', 'Unknown')
                            quota_id = violation.get('quota_id', 'Unknown')
                            print(f"      - {quota_metric}: {quota_id}")
            return False
        elif response.status_code == 400:
            error_detail = response.json()
            print(f"❌ Embedding API lỗi request: {error_detail}")
            return False
        elif response.status_code == 403:
            print("❌ Embedding API bị từ chối (có thể đã hết quota hoặc bị disable)")
            return False
        else:
            print(f"❌ Embedding API error: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout khi gọi Embedding API")
        return False
    except Exception as e:
        print(f"❌ Lỗi khi test Embedding API: {e}")
        return False

def main():
    """Hàm chính"""
    print("🔍 Kiểm tra Google API Key (Gemini)")
    print("=" * 50)
    
    # 1. Load API key
    api_key = load_api_key()
    if not api_key:
        return
    
    print()
    
    # 2. Kiểm tra format cơ bản
    if not check_api_key_basic(api_key):
        return
    
    print()
    
    # 3. Liệt kê models có sẵn
    list_available_models(api_key)
    
    print()
    
    # 4. Test Generate Content API
    generate_works = test_gemini_api(api_key)
    
    print()
    
    # 5. Test Embedding API (quan trọng cho RAG)
    embedding_works = test_embedding_api(api_key)
    
    print()
    
    # 6. Tổng kết
    if generate_works and embedding_works:
        print("🎉 CẢ HAI API ĐỀU HOẠT ĐỘNG BÌNH THƯỜNG!")
        print("✅ Chatbot có thể hoạt động đầy đủ (Chat + RAG)")
        
        # Kiểm tra usage chi tiết
        check_api_quotas(api_key)
    elif generate_works and not embedding_works:
        print("⚠️  CHỈ GENERATE API HOẠT ĐỘNG!")
        print("❌ RAG System sẽ không hoạt động do hết quota embedding")
        print("\n💡 Giải pháp:")
        print("1. Đợi quota embedding reset (hàng ngày)")
        print("2. Upgrade API plan để có quota cao hơn")
        print("3. Sử dụng cache embedding để giảm số lần gọi")
        print("4. Tạm thời disable RAG, chỉ dùng chatbot đơn giản")
    elif not generate_works and embedding_works:
        print("⚠️  CHỈ EMBEDDING API HOẠT ĐỘNG!")
        print("❌ Chatbot không thể trả lời do hết quota generate")
    else:
        print("\n❌ API key có vấn đề!")
        print("\n🔧 Các cách khắc phục:")
        print("1. Kiểm tra API key tại: https://aistudio.google.com/app/apikey")
        print("2. Tạo API key mới nếu cần")
        print("3. Kiểm tra quota và billing")
        print("4. Đảm bảo Gemini API được enable")
        print("5. Thử model khác (gemini-1.5-flash thay vì 2.0)")
        
        print()
        print("📊 Thông tin Quota:")
        print("1. Truy cập: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas")
        print("2. Hoặc: https://aistudio.google.com/app/apikey")
        print("3. Kiểm tra usage tại: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/metrics")

if __name__ == "__main__":
    main()


