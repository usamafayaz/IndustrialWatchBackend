from sqlalchemy import Column,Integer,String, Float
from DBHandler import DBHandler
Base = DBHandler.Base

class Product(Base):
    __tablename__ = "Product"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20))
    inspection_angles = Column(String(15))
    rejection_tolerance = Column(Float)