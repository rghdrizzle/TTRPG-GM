from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, DateTime, Integer, Table


engine = create_engine('postgresql://postgres:password@localhost:5432/postgres')

Base = declarative_base()

class BaseModel(Base):


    __abstract__ = True
    __table__: Table

    id = Column(Integer, unique=True, autoincrement=True, nullable=False, index=True, primary_key=True)


# User table
class Users(BaseModel):
    __tablename__ = "users"
    username = Column(String(250),nullable=False)
    email = Column(String(250), nullable=True)
    password = Column(String(250),nullable=False)
    def __repr__(self):
        return f"<Users(id = '{self.id}',username='{self.username}', email='{self.email}', password='{self.password}')>"
    


Base.metadata.create_all(engine) # This creates all the tables in the engine

# get db session to perform database queries
def get_db_session():
    Session = sessionmaker(bind=engine)
    session = Session()

    return session
