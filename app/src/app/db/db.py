from sqlalchemy import create_engine, Column, Integer, String, DateTime, Table , ForeignKey, JSON
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
    embedding = Column(Vector(768))  # 768 since that's what ollama embed vector dimensions are

### tables related to the campaigns

class Campaign(BaseModel):
    __tablename__ = "campaigns"
    document_id = Column(UUID, ForeignKey("documents.id"))
    summary = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    name        = Column(String)

class Sessions(BaseModel):
    __tablename__ = "sessions"
    campaign_id = Column(UUID, ForeignKey("campaigns.id"))
    created_at = Column(DateTime, default=datetime.now)
    ended_at  = Column(DateTime)
    name        = Column(String)

class Turns(BaseModel):
    __tablename__ = "turns"
    session_id = Column(UUID, ForeignKey("sessions.id"))
    player_msg = Column(String)
    gm_response = Column(String)
    created_at = Column(DateTime, default=datetime.now)

# Todo: work on implementing logic with this and add this into the game itself
class Entities(BaseModel):
    __tablename__ = "entities"
    campaign_id = Column(UUID, ForeignKey("campaigns.id"))
    type = Column(String)
    name = Column(String)
    description = Column(String)
    state          = Column(String)
    created_at = Column(DateTime, default=datetime.now)

class CharacterSheet(BaseModel):
    __tablename__ = "charactersheet"
    campaign_id = Column(UUID, ForeignKey("campaigns.id"))
    user_id     = Column(UUID, ForeignKey("users.id"))
    name        = Column(String, nullable=False)
    level       = Column(Integer, default=1)
    hp          = Column(Integer)
    max_hp      = Column(Integer)
    created_at  = Column(DateTime, default=datetime.now)
    stats       = Column(JSON)   
    inventory   = Column(JSON)   
    traits      = Column(JSON)   
    notes       = Column(String)

class Rooms(BaseModel):
    __tablename__ = "rooms"
    name           = Column(String)
    campaign_id = Column(UUID, ForeignKey("campaigns.id"))
    session_id = Column(UUID, ForeignKey("sessions.id"))
    invite_code = Column(String)
    host_user_id = Column(UUID)
    created_at = Column(DateTime, default=datetime.now)

class Rooom_players(BaseModel):
    __tablename__ = "rooms_players"
    room_id       = Column(UUID, ForeignKey("rooms.id"))
    user_id        = Column(UUID)
    charactersheet_id = Column(UUID)
    joined_at = Column(DateTime, default=datetime.now)

    
Base.metadata.create_all(engine) # This creates all the tables in the engine

# get db session to perform database queries
def get_db_session():
    Session = sessionmaker(bind=engine)
    session = Session()

    return session
