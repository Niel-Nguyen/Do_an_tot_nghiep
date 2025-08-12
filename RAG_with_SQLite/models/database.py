from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey, text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    # Thêm các trường khác nếu cần

class Dish(Base):
    __tablename__ = 'dishes'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)  # Món ăn
    region = Column(String)  # Vùng miền
    ingredients = Column(Text)  # Nguyên liệu
    description = Column(Text)  # Mô tả
    recipe = Column(Text)  # Cách làm/công thức
    price = Column(Float)  # Giá
    unit = Column(String)  # Đơn vị tính
    mood = Column(String)  # Tâm trạng, cảm xúc
    main_or_side = Column(String)  # Chính/vặt
    dry_or_soup = Column(String)  # Khô/nước
    image_url = Column(String)  # Hình ảnh
    veg_or_meat = Column(String)  # Chay/Mặn
    cook_time = Column(Integer)  # Thời gian nấu
    calories = Column(Integer)
    fat = Column(Integer)
    fiber = Column(Integer)
    sugar = Column(Integer)
    protein = Column(Integer)
    nutrient_content = Column(String)

class Bill(Base):
    __tablename__ = 'bills'
    id = Column(Integer, primary_key=True)
    order_id = Column(String, unique=True)  # Mã hóa đơn (UUID)
    user_id = Column(String)  # Có thể là IP hoặc username
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String)
    total_amount = Column(Float)
    note = Column(Text)
    paid_at = Column(DateTime, nullable=True)
    user = relationship('User', primaryjoin="foreign(Bill.user_id)==User.username", viewonly=True)

class BillItem(Base):
    __tablename__ = 'bill_items'
    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey('bills.id'))
    dish_name = Column(String)  # Tên món
    quantity = Column(Integer, default=1)
    price = Column(Float)
    total = Column(Float)
    note = Column(Text)
    bill = relationship('Bill', back_populates='items')

Bill.items = relationship('BillItem', order_by=BillItem.id, back_populates='bill')

class ChatHistory(Base):
    __tablename__ = 'chat_histories'
    id = Column(Integer, primary_key=True)
    # Lưu trực tiếp username/user_id dạng chuỗi để đơn giản hóa tích hợp
    user_id = Column(String)
    message = Column(Text)
    response = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    # Không bắt buộc ràng buộc User để linh hoạt khi chưa có bản ghi users tương ứng

# Khởi tạo engine và session
engine = create_engine('sqlite:///project_data.db', echo=True)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    # Create tables if not present
    Base.metadata.create_all(engine)
    # Lightweight migrations for existing SQLite DBs
    # Ensure bills.paid_at column exists
    try:
        with engine.begin() as conn:
            cols = {row[1] for row in conn.execute(text("PRAGMA table_info(bills)"))}
            if 'paid_at' not in cols:
                conn.execute(text("ALTER TABLE bills ADD COLUMN paid_at DATETIME"))
    except Exception:
        # Best-effort; don't block app startup if PRAGMA/ALTER fails
        pass
