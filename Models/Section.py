from DBHandler import DBHandler
from sqlalchemy import Column, Integer, String

Base = DBHandler.Base
class Section(Base):
    __tablename__ = 'Section'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(25))
    status = Column(Integer)
