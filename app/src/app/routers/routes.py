from fastapi import APIRouter, Depends
from typing import Dict
from app.db.db import get_db_session
from sqlalchemy.orm import Session
from app.controllers.user import UserController
from app.db.db import Document
import app.controllers.campaign as campaign
import app.controllers.sessions as sessions
from app.middleware.auth import get_current_user
from sse_starlette.sse import EventSourceResponse 
from fastapi import Request 
from app.services import rag, gm
router = APIRouter()

protected_router = APIRouter(
    dependencies=[Depends(get_current_user)]
)



@router.post("/register",status_code=200)
async def signup(body: Dict,db: Session = Depends(get_db_session)):
    return UserController(db).register_user(body)

@router.post("/login",status_code=200)
async def signup(body: Dict,db: Session = Depends(get_db_session)):
    return UserController(db).login(body)


@router.get("/health", status_code=200)
async def read_users():
    return {"health":"ok"}

@router.get("/stream")
async def stream(body: Dict, request: Request): 
    async def token_generator(): 
        response = ""
        query = body["query"]
        context = rag.get_context_from_query(query)
        async for token in gm.stream_gm_response(context,query)
            if await request.is_disconnected():
                break
            response += token
            yield {"data": token}

        yield {"data":"[DONE]"}

    return EventSourceResponse(token_generator())


@protected_router.get("/test-auth",status_code=200)
async def test():
    return {"auth-status":"authenticated"}

@protected_router.post("/campaigns/new")
async def get_campaign(body: Dict,session: Session = Depends(get_db_session)):
    documentObj = session.query(Document).filter_by(file_path="pdfs/fist.pdf").first() # temp. Todo: fetch document from selected document from a list when creating new campaign 
    campaign_id = campaign.create_new_campaign(body,documentObj.id)
    return {"id":  campaign_id}

# todo: get campaign by user id
@protected_router.get("/campaigns")
async def get_campaigns_list():
    return campaign.get_campaigns()


@protected_router.get("/campaigns/{id}/sessions")
async def get_sessions_list(id):
    return sessions.get_sessions(id)

@protected_router.post("/campaigns/{id}/sessions/new")
async def get_sessions_list(body: Dict,id):
    return sessions.create_new_session(body,id)

# List rulebooks when creating new campaign

# chat endpoint with campaign id
