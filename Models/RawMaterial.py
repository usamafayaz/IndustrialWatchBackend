from sqlalchemy import Column,Integer,String
from DBHandler import DBHandler
Base = DBHandler.Base

class RawMaterial(Base):
    __tablename__ = "RawMaterial"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20))