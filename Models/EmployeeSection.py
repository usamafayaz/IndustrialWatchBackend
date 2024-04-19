from DBHandler import DBHandler
from sqlalchemy import Column, Integer, DateTime

Base = DBHandler.Base

class EmployeeSection(Base):
    __tablename__ = 'EmployeeSection'
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer)
    section_id = Column(Integer)
    date_time = Column(DateTime)

