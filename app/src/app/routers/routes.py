from fastapi import APIRouter, Depends , WebSocket, WebSocketDisconnect
from typing import Dict
from app.db.db import get_db_session
from sqlalchemy.orm import Session
from app.controllers.user import UserController
from app.db.db import Document
from app.controllers import campaign, sessions, turn as turns, rooms
from app.middleware.auth import get_current_user
from sse_starlette.sse import EventSourceResponse 
from fastapi import Request 
from app.services import rag, gm, classifier, retriever
from app.services.websocket import WebSocketManager
import json
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

# chat endpoint with session id
@protected_router.post("/{session_id}/chat")
async def stream(body: Dict, request: Request,session_id): 
    async def token_generator(session_id): 
        response = ""
        query = body["query"]
        intent = classifier.classify(query)
        context =[]
        campaign_id = sessions.get_campaign_id_from_session()
        for i in range(len(intent.topics)):
            embedded_topic = rag.get_embedding(intent.topics[i])
            topic_context = rag.get_context_from_query(embedded_topic)
            b25_topic = rag.b25_search(intent.topics[i])
            context.append(topic_context)
            for j in range(len(b25_topic)):
                context.append(b25_topic[j].get_text()) #todo: clean this text since it includes noise and metadata
        # embedded_query = rag.get_embedding(query)
        # context = rag.get_context_from_query(embedded_query)
        turnsHistory = turns.get_turns(session_id)
        summarized_turns =""
        if len(turnsHistory["payload"]["turns"])%20 ==0 and len(turnsHistory["payload"]["turns"])>1:
            summarized_turns = gm.summarize_turns(turnsHistory["payload"]["turns"])
            campaign.append_summary(summarized_turns,campaign_id=campaign_id)
        if len(turnsHistory["payload"]["turns"])>=20:
            turnsHistory = summarized_turns
        async for token in gm.stream_gm_response(str(intent.Intent),context,query,turnsHistory):
            if await request.is_disconnected():
                break
            response += token
            yield {"data": token}

        yield {"data":"[DONE]"}
        turns.add_turn(query,response,session_id)
    return EventSourceResponse(token_generator(session_id))


@protected_router.get("/{session_id}/chat/history")
async def get_history(session_id):
    return turns.get_turns(session_id)

@protected_router.post("/campaigns/{id}/sessions/{session_id}/rooms/new")
async def create_room(body: Dict,id):
    return rooms.create_new_room(body,id)

@protected_router.post("/room/{room_id}/join")
async def join_room(body: Dict,id):
    return rooms.add_player_id_to_room(body,id)

socketManager = WebSocketManager() # A SINGLE INSTANCE PER SERVER TO MANAGE SOCKET CONNECTIONS AND IN-MEMORY MAP OF ROOM ID AND CONNECTIONS
@router.websocket("/sessions/{session_id}/rooms/{room_id}/ws")
async def websocket_chat(websocket: WebSocket,room_id):
    await socketManager.add_user_to_room(room_id,websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = {
                "user_id": 1,
                "room_id": room_id,
                "message": data
            }
            await socketManager.broadcast_to_room(room_id, json.dumps(message))

    except WebSocketDisconnect:
        await socketManager.remove_user_from_room(room_id, websocket)

        message = {
            "user_id": 1,
            "room_id": room_id,
            "message": f"User {1} disconnected from room - {room_id}"
        }
        await socketManager.broadcast_to_room(room_id, json.dumps(message))




    # await websocket.accept()
    # while True:
    #     data = await websocket.receive_json()
    #     await websocket.send_json(f"ahhahaha{data}")