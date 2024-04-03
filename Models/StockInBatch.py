from DBHandler import DBHandler
from sqlalchemy import Column,Integer,String
Base = DBHandler.Base

class StockInBatch(Base):
    __tablename__ = "StockInBatch"
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_number = Column(String(40))
    batch_number = Column(String(40))

