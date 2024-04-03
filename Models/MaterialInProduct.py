from DBHandler import DBHandler
from sqlalchemy import Column,Integer
Base = DBHandler.Base

class MaterialInProduct(Base):
    __tablename__="MaterialInProduct"
    id = Column(Integer,primary_key=True,autoincrement=True)
    product_id = Column(Integer)
    raw_material_id = Column(Integer)
    quantity = Column(Integer)
