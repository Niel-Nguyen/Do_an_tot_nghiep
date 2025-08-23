#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.excel_loader import load_dishes_from_excel

def test_image_loading():
    """Test để kiểm tra việc load hình ảnh từ Excel"""
    print("=== Test Image Loading ===")
    
    # Load dishes từ Excel
    dishes = load_dishes_from_excel('data100mon.xlsx')
    
    print(f"Đã load {len(dishes)} món ăn")
    print("\n=== Kiểm tra 10 món đầu tiên ===")
    
    for i, dish in enumerate(dishes[:10]):
        print(f"\n{i+1}. {dish.name}")
        print(f"   Image: {dish.image}")
        print(f"   Has image: {'✅' if dish.image and str(dish.image).strip() and str(dish.image) != 'nan' else '❌'}")
    
    # Đếm số món có hình ảnh
    dishes_with_images = [d for d in dishes if d.image and str(d.image).strip() and str(d.image) != 'nan']
    print(f"\n=== Thống kê ===")
    print(f"Tổng số món: {len(dishes)}")
    print(f"Số món có hình ảnh: {len(dishes_with_images)}")
    print(f"Tỷ lệ có hình ảnh: {len(dishes_with_images)/len(dishes)*100:.1f}%")
    
    # Test hàm insert_dish_images
    print(f"\n=== Test insert_dish_images function ===")
    
    # Import các module cần thiết
    from core.rag_system import rag_system
    from models.ai_models import ai_models
    
    try:
        # Initialize AI models
        ai_models.initialize_models()
        print("✅ AI models initialized")
    except Exception as e:
        print(f"❌ AI models initialization failed: {e}")
        
    # Initialize RAG system
    if rag_system.initialize(dishes):
        print("✅ RAG system initialized")
        
        # Test insert_dish_images với vài món có hình ảnh
        from core.chatbot import insert_dish_images
        
        test_content = """Dưới đây là một số món ngon:
1. Mực ống hấp củ đậu: (45.000 VNĐ/phần) Món này rất ngon
2. Chả giò ngũ vị: (35.000 VNĐ/phần) Món này giòn tan
3. Canh ba màu: (30.000 VNĐ/phần) Canh này thanh mát"""
        
        print("Original content:")
        print(test_content)
        
        result = insert_dish_images(test_content)
        print("\nAfter insert_dish_images:")
        print(result)
        
        # Kiểm tra xem có tag <img> không
        img_count = result.count('<img')
        print(f"\nSố lượng thẻ <img> được chèn: {img_count}")
        
    else:
        print("❌ RAG system initialization failed")

if __name__ == "__main__":
    test_image_loading()
