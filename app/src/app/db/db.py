from sqlalchemy import create_engine, Column, Integer, String, DateTime, Table , ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime

engine = create_engine('postgresql://postgres:password@localhost:5432/postgres')
Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    __table__: Table
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True
    )


# User table
class Users(BaseModel):
    __tablename__ = "users"
    username = Column(String(250),nullable=False)
    email = Column(String(250), nullable=True)
    password = Column(String(250),nullable=False)
    def __repr__(self):
        return f"<Users(id = '{self.id}',username='{self.username}', email='{self.email}', password='{self.password}')>"

class Document(Base):
    __tablename__ = "documents"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True
    )
    title = Column(String, nullable=False)
    system = Column(String, nullable=False)
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.now)

class Chunks(Base):
    __tablename__ = "chunks"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True
    )
    document_id = Column(UUID, ForeignKey("documents.id"))
    content = Column(String)
    section = Column(String)
    embedding = Column(Vector(1024))  # 1024 since that's what cohere vector dimensions are

Base.metadata.create_all(engine) # This creates all the tables in the engine

# get db session to perform database queries
def get_db_session():
    Session = sessionmaker(bind=engine)
    session = Session()

    return session
