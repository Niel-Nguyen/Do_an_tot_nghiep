import qrcode
import io
import base64
from datetime import datetime
from typing import List, Optional, Dict
from models.data_models import Table, Bill, TableSession
import json
import uuid

class TableManager:
    def __init__(self):
        self.tables: Dict[str, Table] = {}
        self.sessions: Dict[str, TableSession] = {}
        self.bills: Dict[str, Bill] = {}
        self._initialize_default_tables()
    
    def _initialize_default_tables(self):
        """Khởi tạo một số bàn mặc định"""
        default_tables = [
            {"name": "Bàn 1", "capacity": 4, "location": "Tầng 1 - Khu A"},
            {"name": "Bàn 2", "capacity": 4, "location": "Tầng 1 - Khu A"},
            {"name": "Bàn 3", "capacity": 6, "location": "Tầng 1 - Khu B"},
            {"name": "Bàn 4", "capacity": 6, "location": "Tầng 1 - Khu B"},
            {"name": "Bàn VIP 1", "capacity": 8, "location": "Tầng 1 - Khu VIP"},
            {"name": "Bàn VIP 2", "capacity": 8, "location": "Tầng 1 - Khu VIP"},
            {"name": "Bàn ngoài trời 1", "capacity": 4, "location": "Ngoài trời - Sân vườn"},
            {"name": "Bàn ngoài trời 2", "capacity": 4, "location": "Ngoài trời - Sân vườn"},
        ]
        
        for table_data in default_tables:
            self.create_table(
                name=table_data["name"],
                capacity=table_data["capacity"],
                location=table_data["location"]
            )
    
    def create_table(self, name: str, capacity: int, location: str) -> Table:
        """Tạo bàn mới"""
        now = datetime.now()
        table = Table(
            id="",
            name=name,
            capacity=capacity,
            status="available",
            qr_code="",
            location=location,
            created_at=now,
            updated_at=now
        )
        
        # Tạo QR code cho bàn
        qr_data = {
            "table_name": table.name,
            "action": "scan_table"
        }
        table.qr_code = self._generate_qr_code(qr_data)
        
        self.tables[table.id] = table
        return table
    
    def _generate_qr_code(self, data: dict) -> str:
        """Tạo QR code từ dữ liệu và trả về base64 string"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        # Nếu có session_token thì tạo URL với token, nếu không thì tạo QR code không hợp lệ
        if data.get("action") == "scan_table" and data.get("session_token"):
            table_id = data.get("table_id", "")
            session_token = data.get("session_token", "")
            qr_data = f"http://192.168.1.112:5000/mobile_menu?table_token={session_token}"
        elif data.get("action") == "scan_table" and data.get("table_id"):
            # Nếu không có token, tạo QR code báo lỗi hoặc trang thông báo
            qr_data = f"http://192.168.1.112:5000/table_closed"
        else:
            qr_data = json.dumps(data, ensure_ascii=False)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    
    def get_table(self, table_id: str) -> Optional[Table]:
        """Lấy thông tin bàn theo ID"""
        return self.tables.get(table_id)
    
    def get_table_by_id(self, table_id: str) -> Optional[Table]:
        """Alias cho get_table - để tương thích với code cũ"""
        return self.get_table(table_id)
    
    def get_all_tables(self) -> List[Table]:
        """Lấy danh sách tất cả bàn"""
        return list(self.tables.values())
    
    def update_table_status(self, table_id: str, status: str) -> bool:
        """Cập nhật trạng thái bàn"""
        if table_id in self.tables:
            self.tables[table_id].status = status
            self.tables[table_id].updated_at = datetime.now()
            return True
        return False
    
    def start_table_session(self, table_id: str, customer_count: int = 0) -> Optional[TableSession]:
        """Bắt đầu phiên làm việc cho bàn"""
        if table_id not in self.tables:
            return None
        
        # Kiểm tra xem bàn có đang hoạt động không
        active_session = self.get_active_session(table_id)
        if active_session:
            return active_session
        
        # Tạo phiên mới
        now = datetime.now()
        session_id = str(uuid.uuid4())
        session_token = str(uuid.uuid4())  # Sinh token mới cho phiên
        session = TableSession(
            id=session_id,
            table_id=table_id,
            table_name=self.tables[table_id].name,
            start_time=now,
            customer_count=customer_count,
            session_token=session_token
        )
        
        # Cập nhật trạng thái bàn
        self.update_table_status(table_id, "occupied")
        
        self.sessions[session.id] = session
        # Cập nhật QR code cho bàn với token mới
        self.tables[table_id].qr_code = self._generate_qr_code({
            "table_id": table_id,
            "session_token": session_token,
            "action": "scan_table"
        })
        return session
    
    def end_table_session(self, table_id: str) -> bool:
        """Kết thúc phiên làm việc cho bàn"""
        active_session = self.get_active_session(table_id)
        if not active_session:
            return False
        
        active_session.end_time = datetime.now()
        active_session.status = "closed"
        # Cập nhật trạng thái bàn
        self.update_table_status(table_id, "available")
        # Khi kết thúc phiên, cập nhật QR code về dạng không có token (hoặc vô hiệu hóa)
        self.tables[table_id].qr_code = self._generate_qr_code({
            "table_id": table_id,
            "action": "scan_table"
        })
        return True
    
    def get_active_session(self, table_id: str) -> Optional[TableSession]:
        """Lấy phiên làm việc đang hoạt động của bàn"""
        for session in self.sessions.values():
            if session.table_id == table_id and session.status == "active":
                return session
        return None
    
    def get_table_bills(self, table_id: str) -> List[Bill]:
        """Lấy danh sách hóa đơn của một bàn"""
        return [bill for bill in self.bills.values() if bill.table_id == table_id]
    
    def create_bill(self, table_id: str, items: List[dict], total_amount: float) -> Bill:
        """Tạo hóa đơn mới cho bàn"""
        table = self.get_table(table_id)
        if not table:
            raise ValueError("Table not found")
        
        now = datetime.now()
        bill_id = str(uuid.uuid4())
        bill = Bill(
            id=bill_id,
            table_id=table_id,
            table_name=table.name,
            items=items,
            total_amount=total_amount,
            status="pending",
            created_at=now,
            updated_at=now
        )
        
        self.bills[bill.id] = bill
        return bill
    
    def update_bill_status(self, bill_id: str, status: str) -> bool:
        """Cập nhật trạng thái hóa đơn"""
        if bill_id in self.bills:
            self.bills[bill_id].status = status
            self.bills[bill_id].updated_at = datetime.now()
            return True
        return False
    
    def get_table_summary(self) -> dict:
        """Lấy tổng quan về tất cả bàn"""
        summary = {
            "total_tables": len(self.tables),
            "available": 0,
            "occupied": 0,
            "reserved": 0,
            "maintenance": 0,
            "active_sessions": 0,
            "total_bills": len(self.bills)
        }
        
        for table in self.tables.values():
            summary[table.status] += 1
        
        summary["active_sessions"] = len([s for s in self.sessions.values() if s.status == "active"])
        
        return summary
    
    def scan_qr_code(self, qr_data: str) -> Optional[dict]:
        """Xử lý khi quét QR code"""
        try:
            data = json.loads(qr_data)
            table_id = data.get("table_id")
            action = data.get("action")
            
            # Kiểm tra xem table_id có tồn tại trong danh sách bàn không
            if action == "scan_table" and table_id:
                # Tìm bàn theo table_id
                table = None
                for t in self.tables.values():
                    if t.id == table_id or t.name == table_id:
                        table = t
                        break
                
                if table:
                    return {
                        "success": True,
                        "table": {
                            "id": table.id,
                            "name": table.name,
                            "capacity": table.capacity,
                            "status": table.status,
                            "location": table.location
                        },
                        "action": "redirect_to_menu",
                        "url": f"/mobile_menu?table_id={table.id}"
                    }
                else:
                    return {"success": False, "error": f"Không tìm thấy bàn với ID: {table_id}"}
            else:
                return {"success": False, "error": "QR code không hợp lệ hoặc thiếu thông tin"}
        except Exception as e:
            return {"success": False, "error": f"Lỗi xử lý QR code: {str(e)}"}
    
    def delete_table(self, table_id: str) -> bool:
        """Xóa bàn khỏi hệ thống"""
        if table_id in self.tables:
            del self.tables[table_id]
            # Xóa luôn các session và bill liên quan nếu cần
            self.sessions = {sid: s for sid, s in self.sessions.items() if s.table_id != table_id}
            self.bills = {bid: b for bid, b in self.bills.items() if b.table_id != table_id}
            return True
        return False

# Khởi tạo instance toàn cục
table_manager = TableManager()
