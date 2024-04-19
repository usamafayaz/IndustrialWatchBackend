from DBHandler import DBHandler
from sqlalchemy import Column, Integer, Date, Time

Base = DBHandler.Base
class Violation(Base):
    __tablename__ = 'Violation'
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer)
    rule_id = Column(Integer)
    date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
