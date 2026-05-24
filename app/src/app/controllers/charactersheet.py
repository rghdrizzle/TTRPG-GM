from app.db import db
from app.db.db import get_db_session
from fastapi import HTTPException, status



session = get_db_session()

def create_new_character(character_info,user_id):

    character = db.CharacterSheet(
        name = character_info["name"],
        user_id = user_id,
        level = character_info["level"],
        hp  = character_info["hp"],
        max_hp = character_info["max_hp"],
        stats = character_info["stats"],
        inventory = character_info["inventory"],
        traits = character_info["traits"],
        notes = character_info["notes"],

    )
    session.add(character)
    session.commit()
    return character.id


def get_character():
    character = session.query(db.Campaign.id, db.Users.id).all()
    character = [
        {
            "id": str(c.id),
            "name": c.name,
            "stats": c.stats,
            "hp": c.hp
        }
        for c in character
    ]

    return {
            "status": 200,
            "message": "Character listed",
            "payload": {
                "character": character
            }
        }