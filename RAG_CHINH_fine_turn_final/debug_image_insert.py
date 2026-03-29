#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('.')

from models.ai_models import ai_models
from core.chatbot import VietnameseFoodChatbot
from utils.excel_loader import load_dishes_from_excel

def test_image_insertion():
    # Khởi tạo AI models
    print("Initializing AI models...")
    ai_models.initialize_models()
    
    # Load dishes
    print("Loading dishes...")
    dishes = load_dishes_from_excel("data100mon.xlsx")
    
    # Khởi tạo chatbot
    print("Initializing chatbot...")
    chatbot = VietnameseFoodChatbot()
    chatbot.initialize(dishes)
    
    # Test content với tên món bị lặp
    test_content = """😋 Món chua ngọt luôn là lựa chọn tuyệt vời để kích thích vị giác. Dưới đây là một vài gợi ý món chua ngọt hấp dẫn tại nhà hàng của chúng tôi:

🥗 MÓN VẶT:
Gỏi gà sứa sả tắc: (45.000 VNĐ/phần) Sứa giòn sần sật, thịt gà dai ngọt, nước gỏi chua chua, rau xanh thanh mát, thêm chút sả tắc thơm lừng, ngon khó cưỡng.
Cá chim kho gừng ớt: (50.000 VNĐ/tô) Cá chim thịt thơm ngon, kho với gừng và ớt tạo nên vị chua ngọt cay nồng hấp dẫn.

Bạn có muốn thử món nào trong những gợi ý trên không ạ?"""

    print("Original content:")
    print(test_content)
    print("\n" + "="*80 + "\n")
    
    # Test insert_dish_images function
    from core.chatbot import insert_dish_images
    result = insert_dish_images(test_content)
    
    print("After insert_dish_images:")
    print(result)
    print(f"\nLength: {len(result)}")

if __name__ == "__main__":
    test_image_insertion()
