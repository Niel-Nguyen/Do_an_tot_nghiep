import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import os

class DatabaseManager:
    def __init__(self, db_path: str = "restaurant.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Khởi tạo database và tạo bảng"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Bảng tables - quản lý bàn
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tables (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    capacity INTEGER DEFAULT 4,
                    status TEXT DEFAULT 'available',
                    qr_code TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Bảng dishes - quản lý món ăn
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dishes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    price REAL NOT NULL,
                    description TEXT,
                    category TEXT,
                    image_url TEXT,
                    is_available BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Bảng orders - quản lý đơn hàng
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    table_id TEXT,
                    user_id TEXT,
                    total_amount REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    payment_time TIMESTAMP,
                    FOREIGN KEY (table_id) REFERENCES tables(id)
                )
            ''')
            
            # Bảng order_items - chi tiết món trong đơn hàng
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    dish_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    total_price REAL NOT NULL,
                    note TEXT,
                    FOREIGN KEY (order_id) REFERENCES orders(id)
                )
            ''')
            
            # Bảng revenue_summary - tổng hợp doanh thu theo ngày
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS revenue_summary (
                    date TEXT PRIMARY KEY,
                    total_revenue REAL DEFAULT 0,
                    orders_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Bảng sessions - phiên làm việc của bàn
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS table_sessions (
                    id TEXT PRIMARY KEY,
                    table_id TEXT NOT NULL,
                    customer_count INTEGER DEFAULT 1,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (table_id) REFERENCES tables(id)
                )
            ''')
            
            conn.commit()
            print("Database initialized successfully!")
    
    # === ORDER METHODS ===
    
    def save_order(self, order_data: Dict[str, Any]) -> bool:
        """Lưu đơn hàng vào database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Lưu order chính
                cursor.execute('''
                    INSERT OR REPLACE INTO orders 
                    (id, table_id, user_id, total_amount, status, note, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    order_data['order_id'],
                    order_data.get('table_id'),
                    order_data.get('user_id'),
                    order_data.get('total_amount', 0),
                    order_data.get('status', 'pending'),
                    order_data.get('note', ''),
                    order_data.get('created_at', datetime.now()),
                    datetime.now()
                ))
                
                # Xóa order_items cũ (nếu update)
                cursor.execute('DELETE FROM order_items WHERE order_id = ?', (order_data['order_id'],))
                
                # Lưu order_items
                if 'items' in order_data:
                    for item in order_data['items']:
                        cursor.execute('''
                            INSERT INTO order_items 
                            (order_id, dish_name, quantity, unit_price, total_price, note)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            order_data['order_id'],
                            item.get('dish') or item.get('name'),
                            item.get('quantity', 1),
                            item.get('unit_price') or item.get('price', 0),
                            item.get('amount') or item.get('total', 0),
                            item.get('note', '')
                        ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error saving order: {e}")
            return False
    
    def update_order_status(self, order_id: str, status: str, payment_time: Optional[datetime] = None) -> bool:
        """Cập nhật trạng thái đơn hàng"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if status == 'paid' and payment_time:
                    cursor.execute('''
                        UPDATE orders 
                        SET status = ?, payment_time = ?, updated_at = ?
                        WHERE id = ?
                    ''', (status, payment_time, datetime.now(), order_id))
                    
                    # Cập nhật revenue summary
                    self.update_revenue_summary(order_id, payment_time.date())
                else:
                    cursor.execute('''
                        UPDATE orders 
                        SET status = ?, updated_at = ?
                        WHERE id = ?
                    ''', (status, datetime.now(), order_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"Error updating order status: {e}")
            return False
    
    def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Lấy đơn hàng theo ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Lấy thông tin order
                cursor.execute('''
                    SELECT o.*, t.name as table_name
                    FROM orders o
                    LEFT JOIN tables t ON o.table_id = t.id
                    WHERE o.id = ?
                ''', (order_id,))
                
                order_row = cursor.fetchone()
                if not order_row:
                    return None
                
                order = dict(order_row)
                
                # Lấy items của order
                cursor.execute('''
                    SELECT * FROM order_items WHERE order_id = ?
                    ORDER BY id
                ''', (order_id,))
                
                items = [dict(row) for row in cursor.fetchall()]
                order['items'] = items
                
                return order
                
        except Exception as e:
            print(f"Error getting order: {e}")
            return None
    
    def get_orders_by_status(self, status: str = None) -> List[Dict[str, Any]]:
        """Lấy danh sách đơn hàng theo trạng thái"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if status:
                    cursor.execute('''
                        SELECT o.*, t.name as table_name
                        FROM orders o
                        LEFT JOIN tables t ON o.table_id = t.id
                        WHERE o.status = ?
                        ORDER BY o.created_at DESC
                    ''', (status,))
                else:
                    cursor.execute('''
                        SELECT o.*, t.name as table_name
                        FROM orders o
                        LEFT JOIN tables t ON o.table_id = t.id
                        ORDER BY o.created_at DESC
                    ''')
                
                orders = []
                for row in cursor.fetchall():
                    order = dict(row)
                    
                    # Lấy items cho mỗi order
                    cursor.execute('''
                        SELECT * FROM order_items WHERE order_id = ?
                    ''', (order['id'],))
                    order['items'] = [dict(item_row) for item_row in cursor.fetchall()]
                    orders.append(order)
                
                return orders
                
        except Exception as e:
            print(f"Error getting orders by status: {e}")
            return []
    
    # === REVENUE METHODS ===
    
    def update_revenue_summary(self, order_id: str, payment_date: str):
        """Cập nhật tổng hợp doanh thu"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Lấy tổng tiền của order
                cursor.execute('SELECT total_amount FROM orders WHERE id = ?', (order_id,))
                result = cursor.fetchone()
                if not result:
                    return
                
                order_total = result[0]
                date_str = str(payment_date)
                
                # Kiểm tra xem đã có record cho ngày này chưa
                cursor.execute('SELECT total_revenue, orders_count FROM revenue_summary WHERE date = ?', (date_str,))
                existing = cursor.fetchone()
                
                if existing:
                    # Cập nhật record hiện tại
                    new_total = existing[0] + order_total
                    new_count = existing[1] + 1
                    cursor.execute('''
                        UPDATE revenue_summary 
                        SET total_revenue = ?, orders_count = ?, updated_at = ?
                        WHERE date = ?
                    ''', (new_total, new_count, datetime.now(), date_str))
                else:
                    # Tạo record mới
                    cursor.execute('''
                        INSERT INTO revenue_summary (date, total_revenue, orders_count)
                        VALUES (?, ?, ?)
                    ''', (date_str, order_total, 1))
                
                conn.commit()
                
        except Exception as e:
            print(f"Error updating revenue summary: {e}")
    
    def get_revenue_by_date(self, date: str) -> Dict[str, Any]:
        """Lấy doanh thu theo ngày"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Lấy tổng hợp doanh thu
                cursor.execute('SELECT * FROM revenue_summary WHERE date = ?', (date,))
                summary_row = cursor.fetchone()
                
                # Lấy chi tiết đơn hàng đã thanh toán trong ngày
                cursor.execute('''
                    SELECT o.*, t.name as table_name
                    FROM orders o
                    LEFT JOIN tables t ON o.table_id = t.id
                    WHERE DATE(o.payment_time) = ? AND o.status = 'paid'
                    ORDER BY o.payment_time DESC
                ''', (date,))
                
                orders = []
                for row in cursor.fetchall():
                    order = dict(row)
                    
                    # Lấy items
                    cursor.execute('SELECT * FROM order_items WHERE order_id = ?', (order['id'],))
                    order['items'] = [dict(item_row) for item_row in cursor.fetchall()]
                    orders.append(order)
                
                result = {
                    'date': date,
                    'total_revenue': summary_row['total_revenue'] if summary_row else 0,
                    'orders_count': summary_row['orders_count'] if summary_row else 0,
                    'orders': orders
                }
                
                return result
                
        except Exception as e:
            print(f"Error getting revenue by date: {e}")
            return {'date': date, 'total_revenue': 0, 'orders_count': 0, 'orders': []}
    
    def get_revenue_summary_stats(self) -> Dict[str, Any]:
        """Lấy thống kê tổng quan doanh thu"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Doanh thu hôm nay
                today = datetime.now().date()
                cursor.execute('SELECT total_revenue, orders_count FROM revenue_summary WHERE date = ?', (str(today),))
                today_data = cursor.fetchone() or (0, 0)
                
                # Doanh thu tháng này
                month = today.strftime('%Y-%m')
                cursor.execute('''
                    SELECT SUM(total_revenue), SUM(orders_count) 
                    FROM revenue_summary 
                    WHERE date LIKE ?
                ''', (f"{month}%",))
                month_data = cursor.fetchone() or (0, 0)
                
                # Tổng doanh thu
                cursor.execute('SELECT SUM(total_revenue), SUM(orders_count) FROM revenue_summary')
                total_data = cursor.fetchone() or (0, 0)
                
                return {
                    'today_revenue': today_data[0] or 0,
                    'today_orders': today_data[1] or 0,
                    'month_revenue': month_data[0] or 0,
                    'month_orders': month_data[1] or 0,
                    'total_revenue': total_data[0] or 0,
                    'total_orders': total_data[1] or 0
                }
                
        except Exception as e:
            print(f"Error getting revenue summary: {e}")
            return {
                'today_revenue': 0, 'today_orders': 0,
                'month_revenue': 0, 'month_orders': 0,
                'total_revenue': 0, 'total_orders': 0
            }

    # === TABLE METHODS ===
    
    def create_table(self, table_id: str, name: str, capacity: int = 4, qr_code: str = "") -> bool:
        """Tạo bàn mới"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO tables (id, name, capacity, qr_code, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (table_id, name, capacity, qr_code, datetime.now().isoformat()))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating table: {e}")
            return False
    
    def get_all_tables(self) -> List[Dict[str, Any]]:
        """Lấy danh sách tất cả bàn"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM tables ORDER BY name')
                
                columns = [description[0] for description in cursor.description]
                tables = []
                
                for row in cursor.fetchall():
                    table_dict = dict(zip(columns, row))
                    tables.append(table_dict)
                
                return tables
                
        except Exception as e:
            print(f"Error getting tables: {e}")
            return []
    
    def update_table_status(self, table_id: str, status: str) -> bool:
        """Cập nhật trạng thái bàn"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tables SET status = ?, updated_at = ? WHERE id = ?
                ''', (status, datetime.now().isoformat(), table_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating table status: {e}")
            return False
    
    def delete_table(self, table_id: str) -> bool:
        """Xóa bàn"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM tables WHERE id = ?', (table_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting table: {e}")
            return False

# Khởi tạo database manager
db_manager = DatabaseManager()
