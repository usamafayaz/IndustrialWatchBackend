from DBHandler import DBHandler
from  sqlalchemy import Column,Integer,String

Base = DBHandler.Base
class User(Base):
    __tablename__='Users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(25))
    password = Column(String(25))
    role = Column(String(20))
    name = Column(String(30))