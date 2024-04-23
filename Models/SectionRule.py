from DBHandler import DBHandler
from sqlalchemy import Column, Integer, Float, Time, DateTime

Base = DBHandler.Base
class SectionRule(Base):
    __tablename__ = 'SectionRule'

    id = Column(Integer, primary_key=True, autoincrement=True)
    section_id = Column(Integer)
    rule_id = Column(Integer)
    fine = Column(Float)
    allowed_time = Column(Time)
    date_time = Column(DateTime)