from sqlalchemy import Column,Integer,String
from DBHandler import DBHandler
Base = DBHandler.Base
class Batch(Base):
    __tablename__ = "Batch"
    batch_number = Column(String(40), primary_key=True)
    product_number = Column(String(40))
    pack_per_batch = Column(Integer)
    piece_per_pack = Column(Integer)
    batch_per_day = Column(Integer)