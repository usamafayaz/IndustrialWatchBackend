from DBHandler import DBHandler
from sqlalchemy import Column,Integer, String
Base = DBHandler.Base

class ProductFormula(Base):
    __tablename__="ProductFormula"
    id = Column(Integer,primary_key=True,autoincrement=True)
    product_number = Column(String(40))
    raw_material_id = Column(Integer)
    quantity = Column(Integer)
    unit = Column(String(5))
