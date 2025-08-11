import os
import json

PAID_BILLS_DIR = 'F:\\d2l_do_an\\d2l-en\\do_an_tot_nghiep\\Do_an_tot_nghiep\\Do_an_tot_nghiep\\RAG_CHINH - mới nhất - có menu - ver2\\paid_bills'

def save_paid_bill(user_name, bill):
    print(f"Saving bill for user: {user_name} at {PAID_BILLS_DIR}")
    os.makedirs(PAID_BILLS_DIR, exist_ok=True)
    path = os.path.join(PAID_BILLS_DIR, f'{user_name}.json')
    bills = load_paid_bills(user_name)
    bills.append(bill)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(bills, f, ensure_ascii=False)
    print(f"Saved bill to {path}")

def load_paid_bills(user_name):
    path = os.path.join(PAID_BILLS_DIR, f'{user_name}.json')
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)