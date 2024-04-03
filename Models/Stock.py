from sqlalchemy import Column,Integer,String, Float
from DBHandler import DBHandler
Base = DBHandler.Base

class Stock(Base):
    __tablename__ = "Stock"
    stock_number = Column(String(40), primary_key=True)
    raw_material_id = Column(Integer)
    quantity = Column(Integer)
    unit = Column(String(5))
    price_per_unit = Column(Integer)
    purchased_date = Column(String(50))
