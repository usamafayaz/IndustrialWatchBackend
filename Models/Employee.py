from DBHandler import DBHandler
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Float

Base = DBHandler.Base


class Employee(Base):
    __tablename__ = 'Employee'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(30))
    salary = Column(Float)
    job_role_id = Column(Integer)
    job_type = Column(String(15))
    date_of_joining = Column(Date)
    gender = Column(String(6))
    user_id = Column(Integer)
