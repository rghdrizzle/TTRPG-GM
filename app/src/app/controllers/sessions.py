from app.db import db
from app.db.db import get_db_session
from fastapi import HTTPException, status



dbSession = get_db_session()

def create_new_session(session_info,campaign_id):

    session = db.Sessions(
        name = session_info["name"],
        campaign_id = campaign_id
    )
    dbSession.add(session)
    dbSession.commit()
    return session.id


def get_sessions(id):
    sessions = dbSession.query(db.Sessions.id, db.Sessions.name,db.Sessions.campaign_id).filter_by(campaign_id=id).all()
    sessions = [
        {
            "id": str(c.id),
            "name": c.name
        }
        for c in sessions
    ]

    return {
            "status": 200,
            "message": "sessions listed",
            "payload": {
                "sessions": sessions
            }
        }