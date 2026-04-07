from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    jwt_secret: str = ""

    @model_validator(mode="after")
    def _default_jwt_secret(self) -> "Settings":
        if not self.jwt_secret:
            self.jwt_secret = self.openai_api_key
        return self

    jwt_algorithm: str = "HS256"
    chroma_persist_path: str = "./chroma_data"
    cors_origins: str = "https://writing-solver-fe.onrender.com"
    frontend_url: str = "https://writing-solver-fe.onrender.com"
    environment: str = "development"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
