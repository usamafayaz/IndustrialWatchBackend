from DBHandler import DBHandler
from sqlalchemy import Column, Integer, String

Base = DBHandler.Base
class EmployeeImages(Base):
    __tablename__ = 'EmployeeImages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer)
    image_url = Column(String)

