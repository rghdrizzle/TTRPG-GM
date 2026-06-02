from app.db import db
from app.db.db import get_db_session
from fastapi import HTTPException, status



session = get_db_session()

def create_new_campaign(campaign_info,document_id):

    campaign = db.Campaign(
        name = campaign_info["name"],
        document_id = document_id
    )
    session.add(campaign)
    session.commit()
    return campaign.id


def get_campaigns():
    campaigns = session.query(db.Campaign.id, db.Campaign.name).all()
    campaigns = [
        {
            "id": str(c.id),
            "name": c.name
        }
        for c in campaigns
    ]

    return {
            "status": 200,
            "message": "campaigns listed",
            "payload": {
                "campaigns": campaigns
            }
        }

def append_summary(summary: str,campaign_id):
    campaign = session.query(db.Campaign).filter_by(id=campaign_id).first()
    if campaign is None:
        return None
    campaign.summary += summary

    session.commit()
    print("Log: summary appended")
    return

