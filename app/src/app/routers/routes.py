from fastapi import APIRouter, Depends
from typing import Dict
from app.db.db import get_db_session
from sqlalchemy.orm import Session
from app.controllers.user import UserController

router = APIRouter()





@router.post("/register",status_code=200)
async def signup(body: Dict,db: Session = Depends(get_db_session)):
    return UserController(db).register_user(body)

@router.post("/login",status_code=200)
async def signup(body: Dict,db: Session = Depends(get_db_session)):
    return UserController(db).login(body)


@router.get("/health", status_code=200)
async def read_users():
    return {"health":"ok"}