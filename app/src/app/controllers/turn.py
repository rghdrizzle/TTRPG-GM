from app.db import db
from app.db.db import get_db_session
from fastapi import HTTPException, status



dbSession = get_db_session()

def create_new_session(turn_info,campaign_id):

    session = db.Turns(
        session_id = turn_info["session_id"],
        player_msg = turn_info["player_msg"],
        gm_response = turn_info["gm_response"]
    )
    dbSession.add(session)
    dbSession.commit()
    return session.id


def get_turns(id):
    turns = dbSession.query(db.Turns.id, db.Turns.session_id,db.Turns.player_msg,db.Turns.created_at,db.Turns.gm_response).filter_by(campaign_id=id).all()
    turns = [
        {
            "id": str(c.id),
            "player_msg": c.playermsg,
            "gm_response": c.gm_response,
            "session_id": c.session_id,
            "created_at": c.created_at
        }
        for c in turns
    ]

    return {
            "status": 200,
            "message": "turns listed",
            "payload": {
                "turns": turns
            }
        }