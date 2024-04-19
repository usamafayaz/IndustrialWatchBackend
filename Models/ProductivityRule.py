from DBHandler import DBHandler
from sqlalchemy import Column, Integer, String

Base = DBHandler.Base
class ProductivityRule(Base):
    __tablename__ = 'ProductivityRule'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20))
