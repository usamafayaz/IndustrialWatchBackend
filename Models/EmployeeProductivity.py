from DBHandler import DBHandler
from sqlalchemy import Column, Integer, Date, Float

Base = DBHandler.Base

class EmployeeProductivity(Base):
    __tablename__ = 'EmployeeProductivity'
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer)
    productivity = Column(Float)
    productivity_month = Column(Date)

