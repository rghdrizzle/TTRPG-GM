import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from app.utils.constants import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(password,hashed_pass):
    return pwd_context.verify(password,hashed_pass)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_after: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    ''' encode dict with provided expiry ion minutes '''
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_after)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt