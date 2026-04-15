from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    jwt_secret: str = ""
    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    # Tavily
    tavily_api_key: str = ""
    # SendGrid
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = ""

    @model_validator(mode="after")
    def _default_jwt_secret(self) -> "Settings":
        if not self.jwt_secret:
            self.jwt_secret = self.openai_api_key
        return self
    jwt_algorithm: str = "HS256"
    chroma_persist_path: str = "./chroma_db"
    cors_origins: str = "http://localhost:4200"
    frontend_url: str = "http://localhost:4200"
    environment: str = "development"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
