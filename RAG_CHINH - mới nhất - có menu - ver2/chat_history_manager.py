import os
import json

CHAT_HISTORY_DIR = 'F:\\d2l_do_an\\d2l-en\\do_an_tot_nghiep\\Do_an_tot_nghiep\\Do_an_tot_nghiep\\RAG_CHINH - mới nhất - có menu - ver2\\chat_histories'

def save_chat_history(user_name, history):
    os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)
    with open(os.path.join(CHAT_HISTORY_DIR, f'{user_name}.json'), 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False)

def load_chat_history(user_name):
    try:
        with open(os.path.join(CHAT_HISTORY_DIR, f'{user_name}.json'), 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []