import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    GOOGLE_APPLICATION_CREDENTIALS: str
    #GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    SECRET_KEY: str
    ALGORITHM: str 
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    
      
    GCP_PROJECT_ID: str
    GCP_BUCKET_NAME: str
    
    CLOUD_PROVIDER: str
    
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool 
    
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5001",
        "http://localhost:5000",
        "http://localhost:8000",
        "https://roda.com"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra="ignore"


settings = Settings()