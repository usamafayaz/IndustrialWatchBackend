from DBHandler import DBHandler
from sqlalchemy import Column, Integer, String, Time

Base = DBHandler.Base
class ViolationImages(Base):
    __tablename__ = 'ViolationImages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    violation_id = Column(Integer)
    image_url = Column(String)
    capture_time = Column(Time)