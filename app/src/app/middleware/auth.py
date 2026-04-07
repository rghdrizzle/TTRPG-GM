from typing import Annotated

import jwt
from app.db.db import Users
from app.db.db import get_db_session
from jwt.exceptions import InvalidTokenError
from starlette.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, Depends, status
from app.utils.constants import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print (payload)
        email: str = payload.get("email")
        if email is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    try:
        with get_db_session() as db:
            user_Obj = db.query(Users).filter(
                Users.email == email
            ).first()
            return user_Obj
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})