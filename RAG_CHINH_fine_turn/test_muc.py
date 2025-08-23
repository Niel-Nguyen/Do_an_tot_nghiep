from utils.excel_loader import load_dishes_from_excel

dishes = load_dishes_from_excel('data100mon.xlsx')

# Tìm các món có chứa 'mực ống'
muc_dishes = [dish for dish in dishes if 'mực ống' in dish.name.lower()]

print('=== Các món mực ống trong database ===')
for dish in muc_dishes:
    print(f'- {dish.name}')

# Tìm các món có chứa 'mực'
print('\n=== Tất cả món mực (10 món đầu) ===')
all_muc = [dish for dish in dishes if 'mực' in dish.name.lower()]
for dish in all_muc[:10]:
    print(f'- {dish.name}')

# Test extract
from core.chatbot import VietnameseFoodChatbot
chatbot = VietnameseFoodChatbot()
dish_name = chatbot._extract_dish_name('Mực ống hấp cũ dậu')
print(f'\nExtracted dish name: "{dish_name}"')
