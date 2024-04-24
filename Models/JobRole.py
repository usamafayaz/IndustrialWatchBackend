from DBHandler import DBHandler
from sqlalchemy import Column, Integer, String
Base = DBHandler.Base


class JobRole(Base):
    __tablename__ = 'JobRole'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(30))
