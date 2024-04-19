from DBHandler import DBHandler
from sqlalchemy import Column, Integer, Time, Date

Base = DBHandler.Base
class Attendance(Base):
    __tablename__ = 'Attendance'
    id = Column(Integer, primary_key=True, autoincrement=True)
    check_in = Column(Time)
    check_out = Column(Time)
    attendance_date = Column(Date)
    employee_id = Column(Integer)

