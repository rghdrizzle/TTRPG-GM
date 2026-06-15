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


def get_rooms(player_info,id):
    player_rooms = dbSession.query(db.Rooom_players).filter_by(user_id=player_info["id"]).all()
    if len(player_rooms)==0:
        return {
            {
            "status": 200,
            "message": "rooms listed according to the user",
            "payload": {
                "rooms": []
            }
        }
        }
    
    room = dbSession.query(db.Rooms.id, db.Rooms.name,db.Rooms.campaign_id,db.Rooms.session_id).filter_by(session_id=id).all()
    room = [
        {
            "id": str(c.id),
            "name": c.name,
            "created_at": c.created_at
        }
        for c in room if c.id in [p.room_id for p in player_rooms]
    ]


    return {
            "status": 200,
            "message": "rooms listed according to the user",
            "payload": {
                "room": room
            }
        }

def add_player_id_to_room(player_info, invite_code):
     room = dbSession.query(db.Rooms).filter_by(invite_code=invite_code).first()

     player = db.Rooom_players(
         room_id = room.id,
         user_id = player_info["id"],
         charactersheet_id = player_info["charactersheet_id"]
     )
     dbSession.add(player)
     dbSession.commit()
     return player.id