from DBHandler import DBHandler
from  sqlalchemy import Column,Integer,String

Base = DBHandler.Base
class User(Base):
    __tablename__='Users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(25))
    password = Column(String(25))
    user_role = Column(String(20))
