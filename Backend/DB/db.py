from sqlalchemy import create_engine,text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus

username = "root"
password = quote_plus("Rahul@123")   # IMPORTANT
host = "127.0.0.1"
port = "3306"
database = "chat_app"

database_url= f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"

engine=create_engine(database_url,pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()



