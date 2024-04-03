from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


class DBHandler:
    Base = declarative_base()
    server = 'GAREEBOOO'
    database = 'IndustrialWatch'
    username = 'sa'
    password = '1234'

    def __init__(self):
        connection_string = f'mssql+pyodbc://{DBHandler.username}:{DBHandler.password}@{DBHandler.server}/{DBHandler.database}?driver=ODBC+Driver+17+for+SQL+Server'
        self.engine = create_engine(connection_string, echo=True)
        self.Session = sessionmaker(bind=self.engine)


def return_session():
    db_handler = DBHandler()
    return db_handler.Session()


def check_database_connection():
    try:
        if DBHandler().engine.connect():
            print("Database connection successful.")
        else:
            print("Database is not Connected")
    except Exception as e:
        print(f"Error connecting to the database: {str(e)}")
        exit()
