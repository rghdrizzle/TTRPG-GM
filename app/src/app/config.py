from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "ttrpg gm"
    database_url: str = "postgresql://postgres:password@localhost:5432/postgres"

    secret_key: str = "lol"
    
    redis_password: str = "password"
    redis_url: str = "redis://localhost:6379"

    class Config:
        env_file =".env"


settings = Settings()