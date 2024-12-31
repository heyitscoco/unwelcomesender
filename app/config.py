from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./gmail_analyzer.db"
    GMAIL_SCOPES: list = ['https://www.googleapis.com/auth/gmail.readonly']
    CREDENTIALS_FILE: str = "credentials.json"
    TOKEN_FILE: str = "token.pickle"
    CORS_ORIGINS: list = ["http://localhost:3000"]

settings = Settings()
