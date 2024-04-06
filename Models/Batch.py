from sqlalchemy import Column,Integer,String,Date,Float
from DBHandler import DBHandler
Base = DBHandler.Base
class Batch(Base):
    __tablename__ = "Batch"
    batch_number = Column(String(40), primary_key=True)
    product_link_id = Column(Integer)
    manufacturing_date = Column(Date)
    batch_yield = Column(Float)
