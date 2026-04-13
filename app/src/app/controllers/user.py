from app.db import db
from app.utils.helpers import get_password_hash
from fastapi import HTTPException, status
from app.utils.helpers import get_password_hash, create_access_token, verify_password



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
        selectedUser = self.db.query(db.Users).filter(db.Users.email == user_info["email"]).first()
        if selectedUser:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'User with email {user_info["email"]} already exits'
            )

        return validated

    def register_user(self,user_info):
        self.validate_user(user_info)
        selectedUser = self.db.query(db.Users).filter(
            db.Users.email == user_info["email"]
        ).first()
        if selectedUser:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'User with email {user_info["email"]} already exits'
            )
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
                "id": str(userObj.id),
                "email": userObj.email,
            }
        }

    def login(self,login_info):
        email = login_info.get("email", None)
        password = login_info.get("password", None)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Missing email in request'
            )

        if not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Missing password in request'
            )
        
        selectedUser = self.db.query(db.Users).filter(db.Users.email == email).first()
        if not selectedUser:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'User with email {email} not found'
            )
        password_hash = verify_password(password=password,hashed_pass=selectedUser.password)
        if  not password_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Password mismatch'
            )
        return {
            "status": 200,
            "message": "User logged in successfully",
            "payload": {
                "token": create_access_token(
                    {
                        "username": selectedUser.username,
                        "id": str(selectedUser.id),
                        "email": selectedUser.email,
                    }
                )
            }
        }