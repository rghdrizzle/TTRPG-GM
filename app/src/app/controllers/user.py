from app.db import db
from app.utils.helpers import get_password_hash
from fastapi import HTTPException, status



class UserController():
    def __init__(self,db):
        self.db = db

    def validate_user(self,user_info):
        required_fields = ["username","email","password"]
        validated = True
        for key in required_fields:
            if key not in user_info:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Missing {key} in request'
                )
        selected_user = self.db.query(db.Users).filter(db.Users.email == user_info["email"]).first()
        if selected_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'User with email {user_info["email"]} already exits'
            )

        return validated

    def register_user(self,user_info):
        self.validate_user(user_info)
        user_info["password"] = get_password_hash(password=user_info["password"])
        userObj = db.Users(**user_info)
        self.db.add(userObj)
        self.db.commit()
        self.db.refresh(userObj)
        return {
            "status": 200,
            "message": "User created successfully",
            "payload": {
                "usernamename": userObj.username,
                "id": userObj.id,
                "email": userObj.email,
            }
        }