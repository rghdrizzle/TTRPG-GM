from app.db import db
from app.db.db import get_db_session
from fastapi import HTTPException, status



session = get_db_session()

def create_new_campaign(document_id):

    campaign = db.Campaign(
        name = "test",
        document_id = document_id
    )
    session.add(campaign)
    session.commit()
    return campaign
