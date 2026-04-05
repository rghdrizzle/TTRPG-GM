from app.config import settings

SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"  # HMAC SHA256 algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = 30 