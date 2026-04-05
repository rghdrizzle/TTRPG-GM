from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "ttrpg gm"
    database_url: str

    secret_key: str
    
    redis_password: str
    redis_url: str = "redis://localhost:6379"

    class Config:
        env_file =".env"


settings = Settings()