from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


engine = create_engine('postgresql://username:password@localhost:5432/dbname')

Base = declarative_base()

# User table
class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(250),nullable=False)
    email = Column(String(250), nullable=True)

    def __repr__(self):
        return f"<Users(id = '{self.id}',username='{self.username}', email='{self.email}')>"
    


Base.metadata.create_all(engine) # This creates all the tables in the engine

# get db session to perform database queries
def get_db_session():
    Session = sessionmaker(bind=engine)
    session = Session()

    return session
