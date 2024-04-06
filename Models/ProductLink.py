from sqlalchemy import Column,Integer,String,Float
from DBHandler import DBHandler
Base = DBHandler.Base

class ProductLink(Base):
    __tablename__ = "ProductLink"
    id = Column(Integer, primary_key=True, autoincrement=True)
    packs_per_batch = Column(Integer)
    piece_per_pack = Column(Integer)
    rejection_tolerance = Column(Float)
    product_number = Column(String(40))
