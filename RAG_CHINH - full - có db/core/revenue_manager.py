from datetime import datetime, date
import json
import os
from typing import Dict, List, Optional
from decimal import Decimal

class RevenueManager:
    def __init__(self):
        self.data_file = 'revenue_data.json'
        self.revenue_data = self.load_revenue_data()
    
    def load_revenue_data(self) -> Dict:
        """Tải dữ liệu doanh thu từ file JSON"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def save_revenue_data(self):
        """Lưu dữ liệu doanh thu vào file JSON"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.revenue_data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Error saving revenue data: {e}")
    
    def add_revenue(self, bill_data: Dict, payment_date: str = None):
        """
        Thêm doanh thu từ hóa đơn đã thanh toán
        
        Args:
            bill_data: Dữ liệu hóa đơn với thông tin món ăn và tổng tiền
            payment_date: Ngày thanh toán (YYYY-MM-DD), nếu None sẽ dùng ngày hiện tại
        """
        if payment_date is None:
            payment_date = date.today().isoformat()
        
        # Tạo entry cho ngày nếu chưa tồn tại
        if payment_date not in self.revenue_data:
            self.revenue_data[payment_date] = {
                'total_revenue': 0,
                'orders_count': 0,
                'orders': []
            }
        
        # Tính tổng tiền hóa đơn
        total_amount = 0
        items = []
        
        # Ưu tiên dùng total từ bill_data nếu có
        if 'total' in bill_data and bill_data['total']:
            total_amount = float(bill_data['total'])
        
        if 'items' in bill_data:
            for item in bill_data['items']:
                # Map các field từ order_manager structure
                name = item.get('dish', '') or item.get('name', '')
                price = float(item.get('unit_price', 0)) or float(item.get('price', 0))
                quantity = int(item.get('quantity', 1))
                item_total = float(item.get('amount', 0)) or float(item.get('total', 0)) or (price * quantity)
                
                items.append({
                    'name': name,
                    'price': price,
                    'quantity': quantity,
                    'total': item_total
                })
            
            # Nếu chưa có total từ bill_data, tính từ items
            if total_amount == 0:
                total_amount = sum(item['total'] for item in items)
        
        # Thêm thông tin đơn hàng
        order_info = {
            'order_id': bill_data.get('id', ''),
            'table_id': bill_data.get('table_id', ''),
            'user_id': bill_data.get('user_id', ''),
            'total': total_amount,  # Đổi từ total_amount thành total để nhất quán
            'total_amount': total_amount,
            'items': items,
            'payment_time': datetime.now().isoformat(),
            'status': 'paid'
        }
        
        # Cập nhật doanh thu ngày
        self.revenue_data[payment_date]['total_revenue'] += total_amount
        self.revenue_data[payment_date]['orders_count'] += 1
        self.revenue_data[payment_date]['orders'].append(order_info)
        
        # Lưu dữ liệu
        self.save_revenue_data()
        
        return True
    
    def get_daily_revenue(self, target_date: str) -> Dict:
        """Lấy doanh thu của một ngày cụ thể"""
        return self.revenue_data.get(target_date, {
            'total_revenue': 0,
            'orders_count': 0,
            'orders': []
        })
    
    def get_monthly_revenue(self, year: int, month: int) -> Dict:
        """Lấy doanh thu của một tháng"""
        month_str = f"{year:04d}-{month:02d}"
        total_revenue = 0
        total_orders = 0
        daily_breakdown = {}
        
        for date_str, data in self.revenue_data.items():
            if date_str.startswith(month_str):
                total_revenue += data['total_revenue']
                total_orders += data['orders_count']
                daily_breakdown[date_str] = data
        
        return {
            'year': year,
            'month': month,
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'daily_breakdown': daily_breakdown
        }
    
    def get_date_range_revenue(self, start_date: str, end_date: str) -> Dict:
        """Lấy doanh thu trong khoảng thời gian"""
        total_revenue = 0
        total_orders = 0
        date_breakdown = {}
        
        for date_str, data in self.revenue_data.items():
            if start_date <= date_str <= end_date:
                total_revenue += data['total_revenue']
                total_orders += data['orders_count']
                date_breakdown[date_str] = data
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'date_breakdown': date_breakdown
        }
    
    def get_revenue_summary(self) -> Dict:
        """Lấy tổng quan doanh thu"""
        total_revenue = 0
        total_orders = 0
        
        for data in self.revenue_data.values():
            total_revenue += data['total_revenue']
            total_orders += data['orders_count']
        
        # Tính doanh thu hôm nay
        today = date.today().isoformat()
        today_revenue = self.get_daily_revenue(today)
        
        # Tính doanh thu tháng này
        now = datetime.now()
        month_revenue = self.get_monthly_revenue(now.year, now.month)
        
        return {
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'today_revenue': today_revenue['total_revenue'],
            'today_orders': today_revenue['orders_count'],
            'month_revenue': month_revenue['total_revenue'],
            'month_orders': month_revenue['total_orders']
        }
    
    def get_all_revenue(self) -> List[Dict]:
        """Lấy tất cả doanh thu đã lưu (để debug)"""
        all_records = []
        for date_str, data in self.revenue_data.items():
            for order in data.get('orders', []):
                record = order.copy()
                record['date'] = date_str
                record['amount'] = record.get('total', 0)
                all_records.append(record)
        
        # Sắp xếp theo thời gian (mới nhất trước)
        all_records.sort(key=lambda x: x.get('date', ''), reverse=True)
        return all_records

# Global instance
revenue_manager = RevenueManager()
