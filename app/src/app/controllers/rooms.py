from app.db import db
from app.db.db import get_db_session
from fastapi import HTTPException, status



dbSession = get_db_session()

def create_new_room(room_info,campaign_id):

    room = db.Sessions(
        name = room_info["name"],
        campaign_id = campaign_id
    )
    dbSession.add(room)
    dbSession.commit()
    return room.id


def get_rooms(id):
    room = dbSession.query(db.Rooms.id, db.Rooms.name,db.Rooms.campaign_id,db.Rooms.session_id).filter_by(session_id=id).all()
    room = [
        {
            "id": str(c.id),
            "name": c.name,
            "created_at": c.created_at
        }
        for c in room
    ]

    return {
            "status": 200,
            "message": "rooms listed",
            "payload": {
                "room": room
            }
        }

def add_player_id_to_room(player_info, room_id):
     player = db.Rooom_players(
         room_id = room_id,
         user_id = player_info["id"],
         charactersheet_id = player_info["charactersheet_id"]
     )
     dbSession.add(player)
     dbSession.commit()
     return player.id