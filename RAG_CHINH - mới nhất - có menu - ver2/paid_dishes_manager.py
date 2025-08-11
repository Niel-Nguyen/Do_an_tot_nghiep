import os
import json

PAID_DISHES_DIR = 'F:\\d2l_do_an\\d2l-en\\do_an_tot_nghiep\\Do_an_tot_nghiep\\Do_an_tot_nghiep\\RAG_CHINH - mới nhất - có menu - ver2\\paid_dishes'

def save_paid_dishes(user_name, dishes):
    os.makedirs(PAID_DISHES_DIR, exist_ok=True)
    path = os.path.join(PAID_DISHES_DIR, f'{user_name}.json')
    try:
        old = load_paid_dishes(user_name)
    except:
        old = []
    # Gộp, loại trùng
    all_dishes = list(set(old + dishes))
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(all_dishes, f, ensure_ascii=False)

def load_paid_dishes(user_name):
    path = os.path.join(PAID_DISHES_DIR, f'{user_name}.json')
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)