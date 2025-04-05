from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String,Date

DATABASE_URL = "sqlite:///C:/Users/suneh/Genova/db_directory/Genova_new.db"  
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class Students(Base):
    __tablename__ = "Students"

    Student_ID = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(String, nullable=False)
    Phone_No = Column(String, nullable=False)
    Guardian_Name = Column(String, nullable=False)
    Program = Column(String, nullable=False)
    Stream = Column(String, nullable=False)
    Email_ID = Column(String, nullable=False, unique=True)
    Gender = Column(String, nullable=False)
    DOB = Column(Date)
    Admission_Status = Column(String)
    ENTRANCE_rank = Column(Integer)
    cgpa = Column(Integer)

class Loan(Base):
    __tablename__ = 'Loan'
    
    Student_ID = Column(Integer)
    Name = Column(String)
    Phone_No = Column(String)
    Email_ID = Column(String)
    Family_Income = Column(Integer)
    Rs_Granted = Column(Integer)
    Loan_Status = Column(String)
    EMI_Amount = Column(Integer)
    Guardian_Name = Column(String)
    Address_Proof = Column(String)
    Income_Proof = Column(String)
    Id_Proof = Column(String)
    Admission_Proof = Column(String)
    Program = Column(String)
    Bank_Name = Column(String)
    Interest = Column(Integer)
    Loan_ID = Column(Integer, primary_key=True)


