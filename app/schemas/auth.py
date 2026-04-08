from pydantic import BaseModel


class GitHubAuthRequest(BaseModel):
    code: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token: str = ""
    token_type: str = "bearer"
    user: dict
