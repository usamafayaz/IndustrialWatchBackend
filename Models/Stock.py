from sqlalchemy import Column,Integer,String, Float,Date
from DBHandler import DBHandler
Base = DBHandler.Base

class Stock(Base):
    __tablename__ = "Stock"
    stock_number = Column(String(40), primary_key=True)
    raw_material_id = Column(Integer)
    quantity = Column(Integer)
    price_per_kg = Column(Float)
    purchased_date = Column(Date)

